# backend/app/schemas/response.py

from pydantic import BaseModel
from typing import Optional, Any


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    database: str
    mock_mode: bool


class ErrorResponse(BaseModel):
    detail: str
    status_code: int
    error_type: Optional[str] = None
    timestamp: Optional[str] = None