# backend/app/schemas/simulation.py

from pydantic import BaseModel, Field, validator, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class SimulationCreate(BaseModel):
    scenario_name: str = Field(..., max_length=255, description="Tên kịch bản")
    rainfall: float = Field(..., gt=0, description="Lượng mưa")
    rainfall_unit: str = Field(..., description="Đơn vị lượng mưa")
    duration: float = Field(..., gt=0, description="Thời gian mưa")
    duration_unit: str = Field(..., description="Đơn vị thời gian")
    additional_params: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @field_validator('rainfall')
    def validate_rainfall(cls, v):
        if v <= 0:
            raise ValueError('Rainfall must be greater than 0')
        if v > 500:
            raise ValueError('Rainfall must be less than 500')
        return v
    
    @field_validator('duration')
    def validate_duration(cls, v):
        if v <= 0:
            raise ValueError('Duration must be greater than 0')
        if v > 72:
            raise ValueError('Duration must be less than 72 hours')
        return v
    
    @field_validator('rainfall_unit')
    def validate_rainfall_unit(cls, v):
        allowed_units = ['mm', 'cm', 'inch']
        if v.lower() not in allowed_units:
            raise ValueError(f'Rainfall unit must be one of: {allowed_units}')
        return v.lower()
    
    @field_validator('duration_unit')
    def validate_duration_unit(cls, v):
        allowed_units = ['minute', 'hour', 'day']
        if v.lower() not in allowed_units:
            raise ValueError(f'Duration unit must be one of: {allowed_units}')
        return v.lower()


class SimulationResponse(BaseModel):
    id: str
    job_id: str
    scenario_name: str
    status: JobStatus
    parameters: Dict[str, Any]
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SimulationStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    scenario_name: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result_url: Optional[str] = None
    result_metadata: Optional[Dict[str, Any]] = None