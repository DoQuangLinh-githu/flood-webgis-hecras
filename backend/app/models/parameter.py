# backend/app/models/parameter.py

import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base

# Tương thích kiểu JSON giữa SQLite và PostgreSQL
JSONType = JSON().with_variant(JSONB, "postgresql")

# Tương thích kiểu UUID giữa SQLite (String/CHAR) và PostgreSQL (UUID native)
UUIDType = String(36).with_variant(PG_UUID(as_uuid=True), "postgresql")


class SimulationParameter(Base):
    __tablename__ = "simulation_parameters"
    
    id = Column(UUIDType, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(UUIDType, ForeignKey("simulation_jobs.id", ondelete="CASCADE"))
    parameter_name = Column(String(100), nullable=False)
    
    # Sử dụng JSONType thay cho JSONB
    parameter_value = Column(JSONType, nullable=False)
    
    unit = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    job = relationship("SimulationJob", back_populates="parameters_list")