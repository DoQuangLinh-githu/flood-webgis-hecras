# backend/app/api/routes/simulations.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from app.core.database import get_db
from app.core.job_manager import JobManager
from app.models.job import SimulationJob, JobStatus
from app.models.user import User
from app.models.result import SimulationResult
from app.schemas.simulation import SimulationCreate, SimulationResponse, SimulationStatusResponse
from app.services.simulation_service import SimulationService
from app.services.hecras_client import HECRASClient

router = APIRouter()


# ============================================
# ENDPOINTS CỤ THỂ - ĐẶT TRƯỚC (ƯU TIÊN CAO)
# ============================================

@router.get("/simulations/hecras/status")
async def get_hecras_status():
    """
    Kiểm tra trạng thái kết nối với HEC-RAS API Service
    """
    is_healthy = HECRASClient.health_check()
    
    if is_healthy:
        info = HECRASClient.get_info()
        return {
            "status": "connected",
            "hecras_service": "available",
            "info": info
        }
    else:
        return {
            "status": "disconnected",
            "hecras_service": "unavailable",
            "message": "Cannot connect to HEC-RAS API Service. Please check the HEC-RAS machine."
        }


@router.post("/simulations/run_hecras", response_model=SimulationResponse)
async def run_hecras_simulation(
    sim_data: SimulationCreate,
    db: Session = Depends(get_db)
):
    """
    Chạy simulation với HEC-RAS thật qua API Service
    
    Luồng xử lý:
    1. Kiểm tra HEC-RAS API Service có sẵn sàng không
    2. Tạo job trong database với status QUEUED
    3. Gửi request đến HEC-RAS API Service
    4. Cập nhật job status dựa trên kết quả
    5. Lưu metadata kết quả nếu thành công
    """
    # 1. Kiểm tra HEC-RAS API Service
    if not HECRASClient.health_check():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="HEC-RAS API Service is not available. Please check the HEC-RAS machine."
        )
    
    # 2. Tạo job trong database (status = QUEUED)
    job = SimulationService.create_job(db, sim_data)
    
    # 3. Gửi request đến HEC-RAS API
    try:
        result = HECRASClient.run_simulation(
            scenario_name=sim_data.scenario_name,
            rainfall=sim_data.rainfall,
            rainfall_unit=sim_data.rainfall_unit,
            duration=sim_data.duration,
            duration_unit=sim_data.duration_unit,
            job_id=job.job_id
        )
    except Exception as e:
        job.status = JobStatus.FAILED.value
        job.error_message = f"Failed to connect to HEC-RAS API: {str(e)}"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"HEC-RAS API error: {str(e)}"
        )
    
    # 4. Cập nhật job status dựa trên kết quả
    if result.get("status") == "completed":
        job.status = JobStatus.COMPLETED.value
        job.completed_at = datetime.now()
        
        # Lưu metadata kết quả
        metadata = result.get("metadata", {})
        if metadata:
            sim_result = SimulationResult(
                job_id=job.id,
                result_type="flood_depth",
                crs=metadata.get("crs"),
                min_value=metadata.get("min_value"),
                max_value=metadata.get("max_value"),
                result_url=result.get("result_url"),
                metadata=metadata
            )
            db.add(sim_result)
        
        db.commit()
        db.refresh(job)
        
        return SimulationResponse(
            id=str(job.id),
            job_id=job.job_id,
            scenario_name=job.scenario_name,
            status=JobStatus(job.status),
            parameters=job.parameters,
            error_message=job.error_message,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at
        )
    else:
        job.status = JobStatus.FAILED.value
        job.error_message = result.get("error", "Unknown HEC-RAS error")
        db.commit()
        db.refresh(job)
        
        return SimulationResponse(
            id=str(job.id),
            job_id=job.job_id,
            scenario_name=job.scenario_name,
            status=JobStatus(job.status),
            parameters=job.parameters,
            error_message=job.error_message,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at
        )


# ============================================
# ENDPOINTS CŨ - GIỮ NGUYÊN (ĐẶT SAU)
# ============================================

@router.post("/simulations", response_model=SimulationResponse, status_code=status.HTTP_201_CREATED)
async def create_simulation(
    sim_data: SimulationCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new simulation job (QUEUED - chờ Agent xử lý)
    
    Đây là endpoint cũ, dùng để tạo job và đưa vào hàng đợi.
    """
    # Generate unique job ID
    job_id = JobManager.generate_job_id()
    
    # Create a default user (for Phase 2, we'll use a system user)
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
    
    # Prepare parameters
    parameters = {
        "rainfall": sim_data.rainfall,
        "rainfall_unit": sim_data.rainfall_unit,
        "duration": sim_data.duration,
        "duration_unit": sim_data.duration_unit,
        "additional_params": sim_data.additional_params
    }
    
    # Create job
    job = SimulationJob(
        job_id=job_id,
        user_id=user.id,
        scenario_name=sim_data.scenario_name,
        status=JobStatus.QUEUED.value,
        parameters=parameters,
        created_at=datetime.now()
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    return SimulationResponse(
        id=str(job.id),
        job_id=job.job_id,
        scenario_name=job.scenario_name,
        status=JobStatus(job.status),
        parameters=job.parameters,
        error_message=job.error_message,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at
    )


@router.get("/simulations", response_model=List[SimulationResponse])
async def get_all_simulations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all simulation jobs
    """
    jobs = db.query(SimulationJob).order_by(
        SimulationJob.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return [
        SimulationResponse(
            id=str(job.id),
            job_id=job.job_id,
            scenario_name=job.scenario_name,
            status=JobStatus(job.status),
            parameters=job.parameters,
            error_message=job.error_message,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at
        )
        for job in jobs
    ]


@router.get("/simulations/{job_id}", response_model=SimulationStatusResponse)
async def get_simulation_status(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get simulation job status and results
    """
    job = db.query(SimulationJob).filter(
        SimulationJob.job_id == job_id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    result_url = None
    result_metadata = None
    
    if job.results:
        latest_result = job.results[-1]
        result_url = latest_result.result_url
        result_metadata = {
            "result_type": latest_result.result_type,
            "crs": latest_result.crs,
            "min_value": latest_result.min_value,
            "max_value": latest_result.max_value,
            "created_at": latest_result.created_at
        }
    
    return SimulationStatusResponse(
        job_id=job.job_id,
        status=JobStatus(job.status),
        scenario_name=job.scenario_name,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
        result_url=result_url,
        result_metadata=result_metadata
    )


@router.get("/simulations/{job_id}/status", response_model=SimulationStatusResponse)
async def get_simulation_status_only(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get simulation job status only (without results)
    """
    job = db.query(SimulationJob).filter(
        SimulationJob.job_id == job_id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    return SimulationStatusResponse(
        job_id=job.job_id,
        status=JobStatus(job.status),
        scenario_name=job.scenario_name,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
        result_url=None,
        result_metadata=None
    )


@router.delete("/simulations/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_simulation(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Cancel a simulation job (only if QUEUED or RUNNING)
    """
    job = db.query(SimulationJob).filter(
        SimulationJob.job_id == job_id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    if job.status in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job with status: {job.status}"
        )
    
    job.status = JobStatus.CANCELLED.value
    job.completed_at = datetime.now()
    db.commit()
    
    return None