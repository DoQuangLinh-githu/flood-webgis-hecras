# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

from app.api.routes import simulations, health
from app.core.config import settings
from app.core.database import engine
from app.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Flood WebGIS HEC-RAS Backend...")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"HEC-RAS API URL: {settings.HECRAS_API_URL}")

    # Create tables (in dev mode)
    if settings.ENVIRONMENT == "development":
        try:
            Base.metadata.create_all(bind=engine)
            print("Database tables ensured")
        except Exception as e:
            print(f"Warning: could not create tables: {e}")

    yield

    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Flood WebGIS HEC-RAS Simulation API",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.cors_methods_list,
    allow_headers=settings.cors_headers_list,
)

# Include routers
app.include_router(simulations.router, prefix="/api", tags=["simulations"])
app.include_router(health.router, prefix="/api", tags=["health"])


# ============================================================
# SERVE FRONTEND (nếu muốn gộp chung 1 service)
# ============================================================

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

if FRONTEND_DIR.exists():
    # Serve static files (css, js)
    app.mount(
        "/static",
        StaticFiles(directory=str(FRONTEND_DIR)),
        name="static",
    )

    from fastapi.responses import FileResponse

    @app.get("/")
    async def serve_frontend():
        return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/api")
async def api_root():
    return {
        "message": "Flood WebGIS HEC-RAS API",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
    }