# backend/app/core/job_manager.py

import uuid
from datetime import datetime
from typing import Optional

from app.models.job import SimulationJob, JobStatus
from app.models.agent import Agent


class JobManager:
    """Manager for simulation jobs"""
    
    @staticmethod
    def generate_job_id() -> str:
        """Generate a unique job ID in format JOB-001"""
        # Get current count from database (simplified for Phase 2)
        # In production, we should query the database for the last job ID
        import random
        return f"JOB-{random.randint(100, 999):03d}"
    
    @staticmethod
    def get_job_status(job: SimulationJob) -> JobStatus:
        """Get job status as enum"""
        return JobStatus(job.status)
    
    @staticmethod
    def can_start_job(job: SimulationJob) -> bool:
        """Check if job can be started"""
        return job.status == JobStatus.QUEUED.value
    
    @staticmethod
    def can_cancel_job(job: SimulationJob) -> bool:
        """Check if job can be cancelled"""
        return job.status in [JobStatus.QUEUED.value, JobStatus.RUNNING.value]
    
    @staticmethod
    def is_completed(job: SimulationJob) -> bool:
        """Check if job is completed"""
        return job.status in [
            JobStatus.COMPLETED.value,
            JobStatus.FAILED.value,
            JobStatus.CANCELLED.value
        ]