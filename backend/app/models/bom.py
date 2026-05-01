import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from app.utils.types import PortableUUID as UUID

from app.database import Base


class BomItem(Base):
    __tablename__ = "bom_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assembly_id = Column(UUID(as_uuid=True), ForeignKey("parts.id"), nullable=False, index=True)
    part_id = Column(UUID(as_uuid=True), ForeignKey("parts.id"), nullable=False)
    quantity = Column(Integer, default=1)
    level = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
