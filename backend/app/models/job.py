# backend/app/models/job.py

import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from app.core.database import Base

# Tương thích UUID / JSON giữa SQLite và PostgreSQL
UUIDType = String(36).with_variant(PG_UUID(as_uuid=True), "postgresql")
JSONType = JSON().with_variant(JSONB, "postgresql")


class JobStatus(str, PyEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class SimulationJob(Base):
    __tablename__ = "simulation_jobs"

    id = Column(UUIDType, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(
        UUIDType,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    scenario_name = Column(String(255), nullable=False)
    status = Column(String(50), default=JobStatus.QUEUED.value, index=True)
    parameters = Column(JSONType, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="jobs")
    parameters_list = relationship(
        "SimulationParameter",
        back_populates="job",
        cascade="all, delete-orphan",
    )
    results = relationship(
        "SimulationResult",
        back_populates="job",
        cascade="all, delete-orphan",
    )