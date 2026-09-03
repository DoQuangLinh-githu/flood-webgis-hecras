# agent/src/config.py

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class AgentSettings(BaseSettings):
    # Agent Identity
    AGENT_NAME: str = "hecras-agent-01"
    AGENT_MACHINE_NAME: str = Field(
        default_factory=lambda: os.environ.get("COMPUTERNAME", "WINDOWS-PC")
    )
    AGENT_VERSION: str = "1.0.0"

    # Backend Connection (lấy từ biến môi trường)
    BACKEND_URL: str = Field(
        default="http://localhost:8000",
        env="BACKEND_URL"
    )
    AGENT_TOKEN: str = Field(
        default="your-agent-secret-token-change-in-production",
        env="AGENT_TOKEN"
    )
    AGENT_API_KEY: str = Field(
        default="your-agent-api-key-change-in-production",
        env="AGENT_API_KEY"
    )

    # Polling Configuration
    POLL_INTERVAL: int = 30
    HEARTBEAT_INTERVAL: int = 60
    JOB_TIMEOUT: int = 3600

    # Working Directory
    WORKING_DIR: str = "C:\\HECRAS\\Jobs"
    MODEL_TEMPLATE_DIR: str = "C:\\HECRAS\\Models\\ModelTemplate"

    # HEC-RAS
    HECRAS_EXECUTABLE: str = "C:\\Program Files\\HEC-RAS\\HEC-RAS.exe"
    HECRAS_VERSION: str = "6.4.1"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/agent.log"
    LOG_MAX_SIZE: int = 10485760
    LOG_BACKUP_COUNT: int = 10

    # Security
    ALLOWED_COMMANDS: List[str] = [
        "mkdir", "copy", "xcopy", "echo", "type", "del", "rmdir"
    ]
    ALLOWED_PATHS: List[str] = [
        "C:\\HECRAS\\Jobs",
        "C:\\HECRAS\\Models"
    ]

    # Mock Mode (lấy từ biến môi trường)
    MOCK_MODE: bool = Field(
        default=True,
        env="MOCK_MODE"
    )
    MOCK_SIMULATION_DELAY: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"

    @field_validator("BACKEND_URL")
    @classmethod
    def validate_backend_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("BACKEND_URL must start with http:// or https://")
        return v.rstrip("/")

    @field_validator("POLL_INTERVAL")
    @classmethod
    def validate_poll_interval(cls, v: int) -> int:
        if v < 5:
            raise ValueError("POLL_INTERVAL must be at least 5 seconds")
        return v


settings = AgentSettings()