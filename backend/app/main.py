# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.routes import simulations, health
from app.core.config import settings
from app.core.database import engine
from app.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Flood WebGIS HEC-RAS Backend...")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'Neon'}")
    yield
    # Shutdown
    print("Shutting down...")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Flood WebGIS HEC-RAS Simulation API",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Include routers
app.include_router(simulations.router, prefix="/api", tags=["simulations"])
app.include_router(health.router, prefix="/api", tags=["health"])

# Import và include jobs router (nếu file tồn tại)
try:
    from app.api.routes import jobs
    app.include_router(jobs.router, prefix="/api", tags=["jobs"])
    print("✅ Jobs router loaded")
except ImportError:
    print("⚠️ Jobs router not found - skipping")

# Import và include agents router (nếu file tồn tại)
try:
    from app.api.routes import agents
    app.include_router(agents.router, prefix="/api", tags=["agents"])
    print("✅ Agents router loaded")
except ImportError:
    print("⚠️ Agents router not found - skipping")

@app.get("/")
async def root():
    return {
        "message": "Flood WebGIS HEC-RAS API",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs"
    }