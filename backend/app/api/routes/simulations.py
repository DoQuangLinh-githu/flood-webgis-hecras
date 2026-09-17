# backend/app/api/routes/simulations.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.models.job import SimulationJob, JobStatus
from app.models.user import User
from app.models.result import SimulationResult
from app.schemas.simulation import (
    SimulationCreate,
    SimulationResponse,
    SimulationStatusResponse,
)
from app.services.simulation_service import SimulationService
from app.services.hecras_client import HECRASClient

router = APIRouter()


# ============================================================
# HEC-RAS STATUS
# ============================================================

@router.get("/simulations/hecras/status")
async def get_hecras_status():
    """Kiểm tra kết nối tới HEC-RAS API Service."""
    is_healthy = HECRASClient.health_check()

    if is_healthy:
        info = HECRASClient.get_info()
        return {
            "status": "connected",
            "hecras_service": "available",
            "info": info,
        }
    return {
        "status": "disconnected",
        "hecras_service": "unavailable",
        "message": "Không kết nối được HEC-RAS API Service.",
    }


# ============================================================
# CHẠY SIMULATION
# ============================================================

@router.post("/simulations/run", response_model=SimulationResponse)
async def run_simulation(
    sim_data: SimulationCreate,
    db: Session = Depends(get_db),
):
    """
    Chạy HEC-RAS simulation.

    Luồng:
      1. Kiểm tra HEC-RAS API Service có sống không.
      2. Tạo job trong DB với status=QUEUED.
      3. Gọi HEC-RAS API /run — nhận ngay job_id.
      4. Trả về ngay (không chờ).
    """
    # 1. Health check
    if not HECRASClient.health_check():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="HEC-RAS API Service không phản hồi.",
        )

    # 2. Tạo job trong DB
    job = SimulationService.create_job(db, sim_data)

    # 3. Gọi HEC-RAS API
    result = HECRASClient.run_simulation(
        scenario_name=sim_data.scenario_name,
        rainfall=sim_data.rainfall,
        rainfall_unit=sim_data.rainfall_unit,
        duration=sim_data.duration,
        duration_unit=sim_data.duration_unit,
        job_id=job.job_id,
    )

    if result.get("status") != "queued":
        job.status = JobStatus.FAILED.value
        job.error_message = result.get("error", "Unknown HEC-RAS error")
        db.commit()
        db.refresh(job)
        return _to_response(job)

    # 4. Lưu status queued
    job.status = JobStatus.QUEUED.value
    db.commit()
    db.refresh(job)

    return _to_response(job)


# ============================================================
# POLL JOB STATUS
# ============================================================

@router.get("/simulations/{job_id}", response_model=SimulationStatusResponse)
async def get_simulation_status(
    job_id: str,
    db: Session = Depends(get_db),
):
    """
    Lấy trạng thái job.

    Nếu job đang chạy, đồng bộ status về DB từ HEC-RAS API.
    """
    job = SimulationService.get_job(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} không tồn tại",
        )

    # Nếu job chưa kết thúc, hỏi HEC-RAS API
    if job.status not in [
        JobStatus.COMPLETED.value,
        JobStatus.FAILED.value,
        JobStatus.CANCELLED.value,
    ]:
        hecras_status = HECRASClient.get_job_status(job_id)
        sync_status = _map_hecras_status(hecras_status)

        if sync_status and sync_status != job.status:
            job.status = sync_status
            if sync_status == JobStatus.RUNNING.value:
                if not job.started_at:
                    job.started_at = datetime.now()
            elif sync_status in [
                JobStatus.COMPLETED.value,
                JobStatus.FAILED.value,
            ]:
                job.completed_at = datetime.now()
                if sync_status == JobStatus.FAILED.value:
                    job.error_message = hecras_status.get(
                        "message", "HEC-RAS failed"
                    )
            db.commit()
            db.refresh(job)

            # Nếu vừa completed, lưu metadata kết quả + trigger extract
            if sync_status == JobStatus.COMPLETED.value:
                _save_result_metadata(db, job, hecras_status)

    # Lấy kết quả (nếu có)
    result_url = None
    result_metadata = None
    if job.results:
        latest = job.results[-1]
        result_url = latest.result_url
        result_metadata = {
            "result_type": latest.result_type,
            "crs": latest.crs,
            "min_value": latest.min_value,
            "max_value": latest.max_value,
            "created_at": latest.created_at,
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
        result_metadata=result_metadata,
    )


# ============================================================
# LIST JOBS
# ============================================================

@router.get("/simulations", response_model=List[SimulationResponse])
async def get_all_simulations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    jobs = db.query(SimulationJob).order_by(
        SimulationJob.created_at.desc()
    ).offset(skip).limit(limit).all()
    return [_to_response(j) for j in jobs]


# ============================================================
# CANCEL JOB
# ============================================================

@router.delete("/simulations/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_simulation(
    job_id: str,
    db: Session = Depends(get_db),
):
    job = SimulationService.get_job(db, job_id)
    if not job:
        raise HTTPException(404, f"Job {job_id} không tồn tại")

    if job.status in [
        JobStatus.COMPLETED.value,
        JobStatus.FAILED.value,
        JobStatus.CANCELLED.value,
    ]:
        raise HTTPException(
            400, f"Không thể cancel job ở trạng thái {job.status}"
        )

    job.status = JobStatus.CANCELLED.value
    job.completed_at = datetime.now()
    db.commit()
    return None


# ============================================================
# GET GEOJSON RESULT
# ============================================================

@router.get("/simulations/{job_id}/geojson")
async def get_simulation_geojson(
    job_id: str,
    db: Session = Depends(get_db),
):
    """
    Trả file GeoJSON kết quả ngập lụt.

    Luồng:
      1. Kiểm tra job tồn tại và COMPLETED.
      2. Gọi HEC-RAS API /extract/{job_id} để tạo GeoJSON.
      3. Tải nội dung GeoJSON qua /geojson/{job_id}.geojson.
      4. Trả về client dưới dạng application/geo+json.
    """
    job = SimulationService.get_job(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} không tồn tại",
        )

    if job.status != JobStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job chưa hoàn thành (status={job.status})",
        )

    # 1. Trigger extract (idempotent — nếu file đã tồn tại, HEC-RAS API trả về nhanh)
    extract_result = HECRASClient.extract_geojson(job_id)

    if extract_result.get("status") != "completed":
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "message": "Extract GeoJSON thất bại",
                "error": extract_result.get("error"),
            },
        )

    # 2. Tải nội dung GeoJSON
    geojson_bytes = HECRASClient.download_geojson(job_id)

    if not geojson_bytes:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Không tải được GeoJSON từ HEC-RAS API.",
        )

    # 3. Trả về
    return Response(
        content=geojson_bytes,
        media_type="application/geo+json",
        headers={
            "Cache-Control": "public, max-age=3600",
            "X-Job-Id": job_id,
        },
    )


# ============================================================
# HELPERS
# ============================================================

def _to_response(job: SimulationJob) -> SimulationResponse:
    return SimulationResponse(
        id=str(job.id),
        job_id=job.job_id,
        scenario_name=job.scenario_name,
        status=JobStatus(job.status),
        parameters=job.parameters,
        error_message=job.error_message,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


def _map_hecras_status(hecras_status: dict) -> str | None:
    """
    Map status từ HEC-RAS API sang status của backend.

    HEC-RAS API v3.0.2 dùng: queued, starting, running, completed, failed
    Backend dùng: QUEUED, RUNNING, PROCESSING, COMPLETED, FAILED, CANCELLED
    """
    hs = (hecras_status.get("status") or "").lower()

    if hs == "queued":
        return JobStatus.QUEUED.value
    if hs in ("starting", "running"):
        return JobStatus.RUNNING.value
    if hs == "completed":
        return JobStatus.COMPLETED.value
    if hs == "failed":
        return JobStatus.FAILED.value
    return None


def _save_result_metadata(db: Session, job: SimulationJob, hecras_status: dict):
    """Lưu metadata kết quả vào DB khi job completed."""
    existing = db.query(SimulationResult).filter(
        SimulationResult.job_id == job.id
    ).first()
    if existing:
        return

    files = hecras_status.get("result_files", [])
    result = SimulationResult(
        job_id=job.id,
        result_type="flood_depth",
        result_url=f"/results/{job.job_id}",
        storage_key=f"results/{job.job_id}",
        crs="EPSG:4326",
        min_value=0.0,
        max_value=None,
        result_metadata={
            "result_files": files,
            "result_directory": hecras_status.get("result_directory"),
            "elapsed_seconds": hecras_status.get("elapsed_seconds"),
        },
    )
    db.add(result)
    db.commit()