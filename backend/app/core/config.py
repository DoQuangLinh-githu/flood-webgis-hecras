# backend/app/core/config.py

import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    # --------------------------------------------------------
    # APPLICATION
    # --------------------------------------------------------
    APP_NAME: str = "Flood WebGIS HEC-RAS"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # --------------------------------------------------------
    # API
    # --------------------------------------------------------
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"

    # --------------------------------------------------------
    # CORS — dùng str để tránh Pydantic parse JSON
    # --------------------------------------------------------
    CORS_ORIGINS: str = "*"
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: str = "GET,POST,PUT,DELETE,PATCH,OPTIONS"
    CORS_ALLOW_HEADERS: str = "Authorization,Content-Type,Accept,X-Requested-With"

    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------
    DATABASE_URL: str = "sqlite:///./test.db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # --------------------------------------------------------
    # SECURITY
    # --------------------------------------------------------
    SECRET_KEY: str = "change-me-in-production"

    # --------------------------------------------------------
    # HEC-RAS INTEGRATION
    # --------------------------------------------------------
    HECRAS_API_URL: str = "http://localhost:8000"

    # --------------------------------------------------------
    # SIMULATION DEFAULTS
    # --------------------------------------------------------
    DEFAULT_RAINFALL_UNIT: str = "mm"
    DEFAULT_DURATION_UNIT: str = "hour"
    MAX_SIMULATION_DURATION: int = 72

    # --------------------------------------------------------
    # HELPERS — convert str -> list
    # --------------------------------------------------------
    @property
    def cors_origins_list(self) -> List[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def cors_methods_list(self) -> List[str]:
        return [m.strip() for m in self.CORS_ALLOW_METHODS.split(",") if m.strip()]

    @property
    def cors_headers_list(self) -> List[str]:
        return [h.strip() for h in self.CORS_ALLOW_HEADERS.split(",") if h.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()