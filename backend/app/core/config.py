# backend/app/core/config.py

import os
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Flood WebGIS HEC-RAS"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"

    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    CORS_ALLOW_HEADERS: List[str] = ["Authorization", "Content-Type", "Accept", "X-Requested-With"]

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40

    # Security
    SECRET_KEY: str = "change-me-in-production"

    # Mock Mode
    MOCK_MODE: bool = False

    # HEC-RAS Integration
    HECRAS_API_URL: str = os.getenv("HECRAS_API_URL", "http://localhost:8000")
    HECRAS_MOCK_MODE: bool = os.getenv("HECRAS_MOCK_MODE", "True").lower() == "true"

    # Simulation defaults
    DEFAULT_RAINFALL_UNIT: str = "mm"
    DEFAULT_DURATION_UNIT: str = "hour"
    MAX_SIMULATION_DURATION: int = 72

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()