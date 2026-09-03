# backend/app/api/routes/jobs.py

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.models.job import SimulationJob, JobStatus
from app.models.agent import Agent

router = APIRouter()


def verify_agent_token(request: Request):
    """Verify agent authentication from request headers"""
    agent_name = request.headers.get("x-agent-name")
    agent_token = request.headers.get("x-agent-token")
    
    if not agent_name or not agent_token:
        raise HTTPException(status_code=401, detail="Missing authentication headers")
    if agent_token != "your-agent-secret-token-change-in-production":
        raise HTTPException(status_code=401, detail="Invalid agent token")
    return agent_name


@router.get("/jobs/pending")
async def get_pending_job(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get a pending job for the agent"""
    agent_name = verify_agent_token(request)
    
    job = db.query(SimulationJob).filter(
        SimulationJob.status == JobStatus.QUEUED.value
    ).order_by(
        SimulationJob.created_at
    ).first()

    if not job:
        return None

    agent = db.query(Agent).filter(Agent.agent_name == agent_name).first()
    if agent:
        agent.status = "BUSY"
        agent.last_seen = datetime.now()
        db.commit()

    return {
        "job_id": job.job_id,
        "scenario_name": job.scenario_name,
        "parameters": job.parameters,
        "created_at": job.created_at.isoformat()
    }


@router.put("/jobs/{job_id}/status")
async def update_job_status(
    job_id: str,
    request: Request,
    status_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update job status"""
    agent_name = verify_agent_token(request)
    
    job = db.query(SimulationJob).filter(
        SimulationJob.job_id == job_id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    new_status = status_data.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="Missing status field")

    job.status = new_status
    if status_data.get("error_message"):
        job.error_message = status_data.get("error_message")

    if new_status == JobStatus.RUNNING.value:
        job.started_at = datetime.now()
    elif new_status in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value]:
        job.completed_at = datetime.now()

    db.commit()
    return {"status": "updated"}


@router.put("/jobs/{job_id}/complete")
async def complete_job(
    job_id: str,
    request: Request,
    complete_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Mark job as completed with results"""
    agent_name = verify_agent_token(request)
    
    job = db.query(SimulationJob).filter(
        SimulationJob.job_id == job_id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job.status = JobStatus.COMPLETED.value
    job.completed_at = datetime.now()

    # Save result
    result_data = complete_data.get("result", {})
    from app.models.result import SimulationResult
    result = SimulationResult(
        job_id=job.id,
        result_type=result_data.get("result_type", "flood_depth"),
        result_url=result_data.get("result_url"),
        storage_key=result_data.get("storage_key"),
        crs=result_data.get("crs"),
        min_value=result_data.get("min_value"),
        max_value=result_data.get("max_value"),
        metadata=result_data.get("metadata")
    )
    db.add(result)

    agent = db.query(Agent).filter(Agent.agent_name == agent_name).first()
    if agent:
        agent.status = "ONLINE"
        agent.last_seen = datetime.now()
        db.commit()

    db.commit()
    return {"status": "completed"}