import os
import sys
import logging
from typing import Optional, List
from datetime import datetime, timedelta
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add current directory and parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)

# Load environment variables from .env file if it exists
env_paths = ['/etc/secrets/.env', os.path.join(parent_dir, '.env')]
env_loaded = False
for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        logger.info(f"Loaded environment from {env_path}")
        env_loaded = True
        break

if not env_loaded:
    logger.warning("No .env file found, using system environment variables")

# Email credentials removed - handled in auth-server

# OTP routes removed - handled in auth-server

from fastapi import (
    FastAPI, UploadFile, File, Form, HTTPException, 
    status, Depends
)
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session

import models, database, schemas, security

from database import get_db

from job_queue import job_queue, JobStatus
from services import (
    document_service, clause_service, chat_service, explainer_service, export_service,
    privacy_service, diff_service, save_upload_file
)

# Create database tables
from database import engine, Base
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Legal Redline Sandbox - API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://legal-redline-sandbox-nine.vercel.app", "http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health endpoint
@app.get("/health")
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Legal Redline API is running"}

# Job management endpoints
@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get job status and result"""
    job = job_queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job.to_dict()



#--------------------------------------------
# CHAT SESSION ENDPOINTS (NO AUTH REQUIRED)
#--------------------------------------------

# NEW: Chat Session Management

@app.post("/api/chat/sessions", response_model=schemas.ChatSession)
def create_chat_session(
    db: Session = Depends(get_db)
):
    """
    Creates a new, empty chat session. For now, allows anonymous sessions.
    """
    # Create session without user association for anonymous access
    new_session = models.ChatSession(user_id=None)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

@app.get("/api/chat/sessions", response_model=List[schemas.ChatSession])
def get_chat_sessions(
    db: Session = Depends(get_db)
):
    """
    Gets all anonymous chat sessions.
    """
    return db.query(models.ChatSession).filter(models.ChatSession.user_id == None).all()

# MODIFIED: Original Chat Endpoints

@app.get("/api/chat/history/{session_id}", response_model=List[schemas.ChatMessage])
def get_chat_history(
    session_id: int, 
    db: Session = Depends(get_db)
):
    """
    Gets all messages for a specific anonymous chat session.
    """
    # Check if session exists (anonymous sessions only)
    session = db.query(models.ChatSession).filter(
        models.ChatSession.id == session_id,
        models.ChatSession.user_id == None
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    messages = db.query(models.ChatMessage).filter(models.ChatMessage.session_id == session_id).order_by(models.ChatMessage.timestamp.asc()).all()
    return messages


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Email validation removed - no longer needed without authentication





# Near the top after imports
import os
import logging
from dotenv import load_dotenv

# Set up logging first
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# Load environment variables early
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
env_path = '/etc/secrets/.env'

if not os.path.exists(env_path):
    logger.warning(f".env file not found at {env_path}, proceeding")
    # raise FileNotFoundError(f".env file not found at {env_path}")

load_dotenv(env_path)

# Email validation removed - no longer needed without authentication

# Remove duplicate logging configuration
# Delete or comment out the following lines that appear later in the file:
# logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)






# otp verification routes 
# app.include_router(otp_router, prefix="/api/otp", tags=["OTP"])





# REMOVED DUPLICATE CODE SECTION (was causing startup errors)
# import os
# import logging  
# from dotenv import load_dotenv

# Set up logging first - COMMENTED OUT (already done at top)
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# Load environment variables early - COMMENTED OUT (already done at top)  
# current_dir = os.path.dirname(os.path.abspath(__file__))
# parent_dir = os.path.dirname(current_dir)
# env_path = '/etc/secrets/.env'

# Duplicate code block removed

# Remove duplicate logging configuration
# Delete or comment out the following lines that appear later in the file:
# logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)



@app.get("/api/jobs")
async def get_all_jobs():
    """Get all jobs (simplified for session-based usage)"""
    jobs = job_queue.get_all_jobs()
    return [job.to_dict() for job in jobs]

# Document processing endpoints
@app.post("/api/chat")
async def chat(
    chat_data: schemas.ChatData,
    db: Session = Depends(get_db)
):
    """
    Receives a user chat message, saves it, 
    and starts a background job for the AI's response.
    Works with anonymous sessions.
    """
    # Check if session exists (anonymous sessions only)
    session = db.query(models.ChatSession).filter(
        models.ChatSession.id == chat_data.session_id,
        models.ChatSession.user_id == None
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
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
        user_id=None,  # Anonymous session
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
    db: Session = Depends(get_db)
):
    """
    Saves a generated clause rewrite (session-based, no user required).
    """
    new_rewrite = models.ClauseRewrite(
        **rewrite_data.dict(),
        user_id=None  # Anonymous session
    )
    db.add(new_rewrite)
    db.commit()
    db.refresh(new_rewrite)
    return new_rewrite

@app.get("/api/rewrites", response_model=List[schemas.ClauseRewrite])
def get_saved_rewrites(
    db: Session = Depends(get_db)
):
    """
    Gets all saved clause rewrites (anonymous sessions).
    """
    return db.query(models.ClauseRewrite).filter(models.ClauseRewrite.user_id == None).order_by(models.ClauseRewrite.created_at.desc()).all()


# MODIFIED: All other job-creating endpoints

# Document processing endpoints
@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...), 
    force_ocr: bool = False
):
    """Upload a PDF/image file and start background processing"""
    file_path = await save_upload_file(file)
    
    job_id = job_queue.create_job(
        job_type="document_processing",
        user_id="session_user",  # Use session-based identifier
        data={"file_path": file_path, "force_ocr": force_ocr, "filename": file.filename}
    )
    
    # Start background processing
    await job_queue.start_job(job_id, document_service.process_document_async)
    
    return {"job_id": job_id, "status": "processing"}

@app.post("/api/rewrite")
async def rewrite_clause(clause_data: dict):
    """Start background clause rewriting"""
    logger.info(f"Rewrite request received: {clause_data.keys()}")
    
    # Debug: Check clause service status
    logger.info(f"ClauseService initialization status: {clause_service.clause_rewriter is not None}")
    
    job_id = job_queue.create_job(
        job_type="clause_rewriting",
        user_id="session_user",
        data=clause_data
    )
    
    logger.info(f"Created rewrite job: {job_id}")
    
    # Start background processing
    await job_queue.start_job(job_id, clause_service.rewrite_clause_async)
    
    logger.info(f"Started rewrite job: {job_id}")
    
    return {"job_id": job_id, "status": "processing"}

@app.post("/api/chat")
async def chat(chat_data: dict):
    """Start background chat processing"""
    job_id = job_queue.create_job(
        job_type="chat",
        user_id="session_user",
        data=chat_data
    )
    
    # Start background processing
    await job_queue.start_job(job_id, chat_service.chat_async)
    
    return {"job_id": job_id, "status": "processing"}

@app.post("/api/explain")
async def explain_term(term_data: dict):
    """Start background term explanation"""
    job_id = job_queue.create_job(
        job_type="explanation",
        user_id="session_user",
        data=term_data
    )
    
    # Start background processing
    await job_queue.start_job(job_id, explainer_service.explain_term_async)
    
    return {"job_id": job_id, "status": "processing"}

@app.post("/api/export")
async def export_report(export_data: dict):
    """Start background export processing"""
    job_id = job_queue.create_job(
        job_type="export",
        user_id="session_user",
        data=export_data
    )
    
    # Start background processing
    await job_queue.start_job(job_id, export_service.export_async)
    
    return {"job_id": job_id, "status": "processing"}

@app.post("/api/diff")
async def generate_diff(diff_data: dict):
    """Generate HTML diff between original and rewritten text"""
    job_id = job_queue.create_job(
        job_type="diff_generation",
        user_id="session_user",
        data=diff_data
    )
    
    # Start background processing
    await job_queue.start_job(job_id, diff_service.generate_diff_async)
    
    return {"job_id": job_id, "status": "processing"}

@app.post("/api/privacy/redact")
async def redact_document(redaction_data: dict):
    """Start background privacy redaction processing"""
    job_id = job_queue.create_job(
        job_type="privacy_redaction",
        user_id="session_user",
        data=redaction_data
    )
    
    # Start background processing
    await job_queue.start_job(job_id, privacy_service.redact_async)
    
    return {"job_id": job_id, "status": "processing"}

@app.post("/api/analyze/clause")
async def analyze_clause_impact(clause_data: dict):
    """Analyze clause impact using contextual explainer"""
    job_id = job_queue.create_job(
        job_type="clause_analysis",
        user_id="session_user",
        data=clause_data
    )
    
    # Start background processing
    await job_queue.start_job(job_id, explainer_service.analyze_clause_async)
    
    return {"job_id": job_id, "status": "processing"}

@app.post("/api/translate/plain")
async def translate_to_plain_english(translation_data: dict):
    """Translate complex legal language to plain English"""
    job_id = job_queue.create_job(
        job_type="plain_translation",
        user_id="session_user",
        data=translation_data
    )
    
    # Start background processing
    await job_queue.start_job(job_id, explainer_service.translate_plain_async)
    
    return {"job_id": job_id, "status": "processing"}

@app.post("/api/historical/context")
async def get_historical_context(context_data: dict):
    """Get historical context and precedents for clauses"""
    job_id = job_queue.create_job(
        job_type="historical_context",
        user_id="session_user",
        data=context_data
    )
    
    # Start background processing
    await job_queue.start_job(job_id, explainer_service.historical_context_async)
    
    return {"job_id": job_id, "status": "processing"}

@app.get("/")
async def root():
    return {"message": "Legal Redline Sandbox API", "docs": "/docs"}

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)