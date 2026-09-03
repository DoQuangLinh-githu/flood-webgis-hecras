# backend/app/models/result.py

import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base

# Tương thích kiểu JSON giữa SQLite và PostgreSQL
JSONType = JSON().with_variant(JSONB, "postgresql")

# Tương thích kiểu UUID giữa SQLite (String) và PostgreSQL (UUID native)
UUIDType = String(36).with_variant(PG_UUID(as_uuid=True), "postgresql")


class SimulationResult(Base):
    __tablename__ = "simulation_results"
    
    id = Column(UUIDType, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(UUIDType, ForeignKey("simulation_jobs.id", ondelete="CASCADE"))
    result_type = Column(String(50), nullable=False)
    result_url = Column(Text, nullable=True)
    storage_key = Column(String(255), nullable=True)
    crs = Column(String(50), nullable=True)
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    
    # Đổi tên thuộc tính Python thành result_metadata 
    # Cột dưới DB vẫn giữ nguyên tên "metadata", sử dụng JSONType thay vì JSONB
    result_metadata = Column("metadata", JSONType, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    job = relationship("SimulationJob", back_populates="results")