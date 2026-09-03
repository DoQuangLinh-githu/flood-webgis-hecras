# backend/app/models/audit.py

import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base

# Tương thích kiểu JSON giữa SQLite và PostgreSQL
JSONType = JSON().with_variant(JSONB, "postgresql")

# Tương thích kiểu UUID giữa SQLite (String) và PostgreSQL (UUID native)
UUIDType = String(36).with_variant(PG_UUID(as_uuid=True), "postgresql")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUIDType, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUIDType, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    action = Column(String(100), nullable=False)
    job_id = Column(UUIDType, ForeignKey("simulation_jobs.id", ondelete="SET NULL"), nullable=True)
    
    # Sử dụng JSONType thay cho JSONB
    audit_metadata = Column("metadata", JSONType, nullable=True)
    
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")