# backend/app/services/simulation_service.py

from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

from app.models.job import SimulationJob, JobStatus
from app.models.user import User
from app.models.result import SimulationResult
from app.schemas.simulation import SimulationCreate
from app.core.job_manager import JobManager
from app.utils.validators import validate_simulation_parameters


class SimulationService:
    """Service for simulation operations"""
    
    @staticmethod
    def create_job(db: Session, sim_data: SimulationCreate, user_id: Optional[uuid.UUID] = None) -> SimulationJob:
        """Create a new simulation job"""
        # Validate parameters
        validated_params = validate_simulation_parameters(sim_data.dict())
        
        # Generate job ID
        job_id = JobManager.generate_job_id()
        
        # Get or create user
        if user_id is None:
            user = db.query(User).filter(User.email == "system@example.com").first()
            if not user:
                user = User(
                    email="system@example.com",
                    username="system",
                    password_hash="system_hash",
                    role="admin"
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            user_id = user.id
        
        # Create job
        job = SimulationJob(
            job_id=job_id,
            user_id=user_id,
            scenario_name=sim_data.scenario_name,
            status=JobStatus.QUEUED.value,
            parameters=validated_params,
            created_at=datetime.now()
        )
        
        db.add(job)
        db.commit()
        db.refresh(job)
        
        return job
    
    @staticmethod
    def get_job(db: Session, job_id: str) -> Optional[SimulationJob]:
        """Get job by job_id"""
        return db.query(SimulationJob).filter(
            SimulationJob.job_id == job_id
        ).first()
    
    @staticmethod
    def get_all_jobs(db: Session, skip: int = 0, limit: int = 100) -> list[SimulationJob]:
        """Get all jobs with pagination"""
        return db.query(SimulationJob).order_by(
            SimulationJob.created_at.desc()
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_status(db: Session, job: SimulationJob, status: JobStatus) -> SimulationJob:
        """Update job status"""
        job.status = status.value
        
        if status == JobStatus.RUNNING:
            job.started_at = datetime.now()
        elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            job.completed_at = datetime.now()
        
        db.commit()
        db.refresh(job)
        return job
    
    @staticmethod
    def save_result(
        db: Session, 
        job: SimulationJob, 
        result_type: str,
        result_url: str,
        storage_key: str,
        crs: str,
        min_value: float,
        max_value: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SimulationResult:
        """Save simulation result"""
        result = SimulationResult(
            job_id=job.id,
            result_type=result_type,
            result_url=result_url,
            storage_key=storage_key,
            crs=crs,
            min_value=min_value,
            max_value=max_value,
            metadata=metadata,
            created_at=datetime.now()
        )
        
        db.add(result)
        db.commit()
        db.refresh(result)
        
        # Update job status to COMPLETED
        SimulationService.update_status(db, job, JobStatus.COMPLETED)
        
        return result