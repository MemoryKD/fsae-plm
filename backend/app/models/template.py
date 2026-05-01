import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from app.utils.types import PortableUUID as UUID, PortableJSON as JSONB

from app.database import Base


class PartNumberTemplate(Base):
    __tablename__ = "part_number_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    prefix = Column(String(20))
    separator = Column(String(5), default="-")
    digit_count = Column(Integer, default=3)
    subsystem_codes = Column(JSONB, default=dict)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
