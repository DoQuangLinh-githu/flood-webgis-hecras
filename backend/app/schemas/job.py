# backend/app/schemas/job.py

from pydantic import BaseModel
from typing import Optional, Dict, Any


class JobUpdate(BaseModel):
    status: str
    error_message: Optional[str] = None


class JobComplete(BaseModel):
    status: str = "COMPLETED"
    result: Dict[str, Any]


class JobPendingResponse(BaseModel):
    job_id: str
    scenario_name: str
    parameters: Dict[str, Any]
    created_at: strcd