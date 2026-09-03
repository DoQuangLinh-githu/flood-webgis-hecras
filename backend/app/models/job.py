# backend/app/models/job.py

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from enum import Enum as PyEnum

from app.core.database import Base


class JobStatus(str, PyEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class SimulationJob(Base):
    __tablename__ = "simulation_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(String(50), unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    scenario_name = Column(String(255), nullable=False)
    status = Column(String(50), default=JobStatus.QUEUED.value)
    parameters = Column(JSONB, nullable=False)
    error_message = Column(Text, nullable=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="jobs")
    agent = relationship("Agent", back_populates="jobs")
    parameters_list = relationship("SimulationParameter", back_populates="job", cascade="all, delete-orphan")
    results = relationship("SimulationResult", back_populates="job", cascade="all, delete-orphan")