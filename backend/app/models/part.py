import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Part(Base):
    __tablename__ = "parts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    part_number = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    type = Column(String(20), nullable=False)
    subsystem = Column(String(50))
    template_id = Column(UUID(as_uuid=True), ForeignKey("part_number_templates.id"), nullable=True)
    current_version = Column(String(10))
    workflow_state = Column(String(50), default="设计中")
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
