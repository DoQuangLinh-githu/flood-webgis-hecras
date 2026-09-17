# backend/app/api/routes/health.py

from fastapi import APIRouter
from datetime import datetime

from app.core.config import settings
from app.services.hecras_client import HECRASClient

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check cho backend + HEC-RAS API."""
    hecras_ok = HECRASClient.health_check()

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": settings.ENVIRONMENT,
        "version": settings.APP_VERSION,
        "hecras_api": {
            "url": settings.HECRAS_API_URL,
            "connected": hecras_ok,
        },
    }