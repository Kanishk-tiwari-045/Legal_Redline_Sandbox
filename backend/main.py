import os
import sys
import logging
from typing import Optional, List
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)

# Add current directory and parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)

# Load environment variables from .env file
load_dotenv(os.path.join(parent_dir, '.env'))

from fastapi import (
    FastAPI, UploadFile, File, HTTPException, 
    status, Depends
)
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt

from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, database, schemas, security

from .database import get_db
from job_queue import job_queue, JobStatus
from services import (
    document_service, clause_service, chat_service, explainer_service, export_service,
    privacy_service, diff_service, save_upload_file
)

app = FastAPI(title="Legal Redline Sandbox - API")

# Create database tables
# This line tells SQLAlchemy to create the tables if they don't exist
models.Base.metadata.create_all(bind=database.engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# This tells FastAPI where the login endpoint is
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

#--------------------------------------------
# 1. NEW: AUTHENTICATION ENDPOINTS
#--------------------------------------------

@app.post("/api/users/register", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    """
    # Check if user already exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash the password
    hashed_password = security.get_password_hash(user.password)
    
    # Create new user object
    new_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        last_active=datetime.utcnow()
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@app.post("/api/auth/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """
    Log in a user (using email as the 'username') and return a JWT token.
    """
    # Find user by email (which is what form_data.username will contain)
    user = db.query(models.User).filter(models.User.email == form_data.username).first()

    # Check if user exists and password is correct
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create the access token
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    # Update last_active time
    user.last_active = datetime.utcnow()
    db.commit()
    
    return {"access_token": access_token, "token_type": "bearer"}


#--------------------------------------------
# 2. NEW: "GET CURRENT USER" DEPENDENCY
#--------------------------------------------

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> models.User:
    """
    Dependency to get the current logged-in user from a token.
    This will be used to protect all other endpoints.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    
    return user


#--------------------------------------------
# 3. NEW & MODIFIED: PROTECTED ENDPOINTS
#--------------------------------------------

# NEW: Chat Session Management

@app.post("/api/chat/sessions", response_model=schemas.ChatSession)
def create_chat_session(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """
    Creates a new, empty chat session for the logged-in user.
    """
    new_session = models.ChatSession(user_id=current_user.id)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

@app.get("/api/chat/sessions", response_model=List[schemas.ChatSession])
def get_chat_sessions(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """
    Gets all chat sessions for the logged-in user.
    """
    return db.query(models.ChatSession).filter(models.ChatSession.user_id == current_user.id).all()

# MODIFIED: Original Chat Endpoints

@app.get("/api/chat/history/{session_id}", response_model=List[schemas.ChatMessage])
def get_chat_history(
    session_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Gets all messages for a specific chat session.
    Ensures the user owns this session.
    """
    # NEW Security Check
    session = db.query(models.ChatSession).filter(
        models.ChatSession.id == session_id,
        models.ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found or you do not have permission"
        )
    # END Security Check
    
    messages = db.query(models.ChatMessage).filter(models.ChatMessage.session_id == session_id).order_by(models.ChatMessage.timestamp.asc()).all()
    return messages

@app.post("/api/chat")
async def chat(
    chat_data: schemas.ChatData,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Receives a user chat message, saves it, 
    and starts a background job for the AI's response.
    Ensures the user owns the chat session.
    """
    # NEW Security Check
    session = db.query(models.ChatSession).filter(
        models.ChatSession.id == chat_data.session_id,
        models.ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found or you do not have permission"
        )
    # END Security Check
    
    # STEP 1: Save the USER's message immediately
    try:
        db_message = models.ChatMessage(
            session_id=chat_data.session_id,
            message_content=chat_data.prompt,
            is_from_user=True
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        logger.info(f"Saved user message {db_message.id} to session {chat_data.session_id}")
    
    except Exception as e:
        logger.error(f"Failed to save user chat message: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail="Could not save user message to database."
        )

    # STEP 2: Start the background job
    job_id = job_queue.create_job(
        job_type="chat",
        user_id=current_user.id,
        data={
            "chat_data": chat_data.dict(), 
            "user_message_id": db_message.id,
            "session_id": chat_data.session_id
        }
    )
    
    await job_queue.start_job(job_id, chat_service.chat_async)
    
    return {"job_id": job_id, "status": "processing"}


# NEW: Saved Clause Rewrites

@app.post("/api/rewrites", response_model=schemas.ClauseRewrite)
def save_clause_rewrite(
    rewrite_data: schemas.ClauseRewriteCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Saves a generated clause rewrite to the user's account.
    """
    new_rewrite = models.ClauseRewrite(
        **rewrite_data.dict(),
        user_id=current_user.id
    )
    db.add(new_rewrite)
    db.commit()
    db.refresh(new_rewrite)
    return new_rewrite

@app.get("/api/rewrites", response_model=List[schemas.ClauseRewrite])
def get_saved_rewrites(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Gets all saved clause rewrites for the logged-in user.
    """
    return db.query(models.ClauseRewrite).filter(models.ClauseRewrite.user_id == current_user.id).order_by(models.ClauseRewrite.created_at.desc()).all()


# MODIFIED: All other job-creating endpoints

@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...), 
    force_ocr: bool = False,
    current_user: models.User = Depends(get_current_user)
):
    file_path = await save_upload_file(file)
    
    job_id = job_queue.create_job(
        job_type="document_processing",
        user_id=current_user.id, 
        data={"file_path": file_path, "force_ocr": force_ocr, "filename": file.filename}
    )
    
    await job_queue.start_job(job_id, document_service.process_document_async)
    
    return {"job_id": job_id, "status": "processing"}

@app.post("/api/rewrite")
async def rewrite_clause(
    clause_data: dict,
    current_user: models.User = Depends(get_current_user)
):
    job_id = job_queue.create_job(
        job_type="clause_rewriting",
        user_id=current_user.id,
        data=clause_data
    )
    
    await job_queue.start_job(job_id, clause_service.rewrite_clause_async)
    
    return {"job_id": job_id, "status": "processing"}

@app.post("/api/explain")
async def explain_term(
    term_data: dict,
    current_user: models.User = Depends(get_current_user)
):
    """Start background term explanation"""
    job_id = job_queue.create_job(
        job_type="explanation",
        user_id=current_user.id,
        data=term_data
    )
    
    # Start background processing
    await job_queue.start_job(job_id, explainer_service.explain_term_async)
    
    return {"job_id": job_id, "status": "processing"}

@app.post("/api/export")
async def export_report(
    export_data: dict,
    current_user: models.User = Depends(get_current_user)
):
    """Start background export processing"""
    job_id = job_queue.create_job(
        job_type="export",
        user_id=current_user.id,
        data=export_data
    )
    
    # Start background processing
    await job_queue.start_job(job_id, export_service.export_async)
    
    return {"job_id": job_id, "status": "processing"}

@app.post("/api/diff")
async def generate_diff(
    diff_data: dict,
    current_user: models.User = Depends(get_current_user)
):
    """Generate HTML diff between original and rewritten text"""
    job_id = job_queue.create_job(
        job_type="diff_generation",
        user_id=current_user.id,
        data=diff_data
    )
    
    # Start background processing
    await job_queue.start_job(job_id, diff_service.generate_diff_async)
    
    return {"job_id": job_id, "status": "processing"}

@app.post("/api/privacy/redact")
async def redact_document(
    redaction_data: dict,
    current_user: models.User = Depends(get_current_user)
):
    """Start background privacy redaction processing"""
    job_id = job_queue.create_job(
        job_type="privacy_redaction",
        user_id=current_user.id,
        data=redaction_data
    )
    
    # Start background processing
    await job_queue.start_job(job_id, privacy_service.redact_async)
    
    return {"job_id": job_id, "status": "processing"}

@app.post("/api/analyze/clause")
async def analyze_clause_impact(
    clause_data: dict,
    current_user: models.User = Depends(get_current_user)
):
    """Analyze clause impact using contextual explainer"""
    job_id = job_queue.create_job(
        job_type="clause_analysis",
        user_id=current_user.id,
        data=clause_data
    )
    
    # Start background processing
    await job_queue.start_job(job_id, explainer_service.analyze_clause_async)
    
    return {"job_id": job_id, "status": "processing"}

@app.post("/api/translate/plain")
async def translate_to_plain_english(
    translation_data: dict,
    current_user: models.User = Depends(get_current_user)
):
    """Translate complex legal language to plain English"""
    job_id = job_queue.create_job(
        job_type="plain_translation",
        user_id=current_user.id,
        data=translation_data
    )
    
    # Start background processing
    await job_queue.start_job(job_id, explainer_service.translate_plain_async)
    
    return {"job_id": job_id, "status": "processing"}

@app.post("/api/historical/context")
async def get_historical_context(
    context_data: dict,
    current_user: models.User = Depends(get_current_user)
):
    """Get historical context and precedents for clauses"""
    job_id = job_queue.create_job(
        job_type="historical_context",
        user_id=current_user.id,
        data=context_data
    )
    
    # Start background processing
    await job_queue.start_job(job_id, explainer_service.historical_context_async)
    
    return {"job_id": job_id, "status": "processing"}

# Unchanged Endpoints (mostly)

@app.get("/health")
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Legal Redline API is running"}

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    # Note: This is not user-protected. Anyone with a job ID can see the status.
    # This is usually fine, but you could add protection if you want.
    job = job_queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job.to_dict()

@app.get("/api/jobs")
async def get_all_jobs(current_user: models.User = Depends(get_current_user)):
    """Get all jobs (now filtered by user)"""
    # Get all jobs from the queue
    all_jobs = job_queue.get_all_jobs()
    
    # Filter them in Python to only show jobs belonging to the current user
    user_jobs = [j for j in all_jobs if j.user_id == current_user.id]
    
    return [job.to_dict() for job in user_jobs]

@app.get("/")
async def root():
    return {"message": "Legal Redline Sandbox API", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
