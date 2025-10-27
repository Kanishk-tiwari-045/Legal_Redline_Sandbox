import asyncio
import json
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"

class Job:
    def __init__(self, job_id: str, job_type: str, user_id: str, data: Dict[str, Any]):
        self.job_id = job_id
        self.job_type = job_type
        self.user_id = user_id
        self.status = JobStatus.PENDING
        self.data = data
        self.result = None
        self.error = None
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.completed_at = None
        self.progress = 0

    def to_dict(self):
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "user_id": self.user_id,
            "status": self.status,
            "data": self.data,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress
        }

class InMemoryJobQueue:
    """Simple in-memory job queue for prototype. In production, use Redis/Celery."""
    
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        
    def create_job(self, job_type: str, user_id: str, data: Dict[str, Any]) -> str:
        job_id = str(uuid.uuid4())
        job = Job(job_id, job_type, user_id, data)
        self.jobs[job_id] = job
        logger.info(f"Created job {job_id} of type {job_type} for user {user_id}")
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Job]:
        return self.jobs.get(job_id)
    
    def get_user_jobs(self, user_id: str) -> list[Job]:
        return [job for job in self.jobs.values() if job.user_id == user_id]
    
    def get_all_jobs(self) -> list[Job]:
        return list(self.jobs.values())
    
    async def start_job(self, job_id: str, executor_func):
        job = self.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        if job.status != JobStatus.PENDING:
            raise ValueError(f"Job {job_id} is not pending")
        
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        
        # Create async task
        task = asyncio.create_task(self._execute_job(job, executor_func))
        self.running_tasks[job_id] = task
        
        return task
    
    async def _execute_job(self, job: Job, executor_func):
        try:
            logger.info(f"Starting execution of job {job.job_id}")
            result = await executor_func(job)
            job.result = result
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.progress = 100
            logger.info(f"Job {job.job_id} completed successfully")
        except Exception as e:
            logger.error(f"Job {job.job_id} failed: {str(e)}")
            job.error = str(e)
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
        finally:
            if job.job_id in self.running_tasks:
                del self.running_tasks[job.job_id]
    
    def update_progress(self, job_id: str, progress: int):
        job = self.get_job(job_id)
        if job:
            job.progress = progress

# Global job queue instance
job_queue = InMemoryJobQueue()