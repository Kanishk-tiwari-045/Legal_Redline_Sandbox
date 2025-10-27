import os
import sys
from typing import Optional
from dotenv import load_dotenv

# Add current directory and parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)

# Load environment variables from .env file
load_dotenv(os.path.join(parent_dir, '.env'))

from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from job_queue import job_queue, JobStatus
from services import (
    document_service, clause_service, chat_service, explainer_service, export_service,
    privacy_service, diff_service, save_upload_file
)

app = FastAPI(title="Legal Redline Sandbox - API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173"],
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

@app.get("/api/jobs")
async def get_all_jobs():
    """Get all jobs (simplified for session-based usage)"""
    jobs = job_queue.get_all_jobs()
    return [job.to_dict() for job in jobs]

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
    job_id = job_queue.create_job(
        job_type="clause_rewriting",
        user_id="session_user",
        data=clause_data
    )
    
    # Start background processing
    await job_queue.start_job(job_id, clause_service.rewrite_clause_async)
    
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)