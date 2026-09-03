# backend/app/api/routes/health.py

from fastapi import APIRouter
from datetime import datetime

from app.core.config import settings
from app.core.database import check_db_connection
from app.schemas.response import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    """
    # Check database connection
    db_healthy = check_db_connection()
    database_status = "healthy" if db_healthy else "unhealthy"
    
    return HealthResponse(
        status="healthy" if db_healthy else "degraded",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        database=database_status,
        mock_mode=settings.MOCK_MODE
    )