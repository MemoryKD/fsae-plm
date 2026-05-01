import uuid
from datetime import datetime
from sqlalchemy import Column, String, BigInteger, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Version(Base):
    __tablename__ = "versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    part_id = Column(UUID(as_uuid=True), ForeignKey("parts.id"), nullable=False, index=True)
    version_number = Column(String(10), nullable=False)
    file_path = Column(String(500))
    file_size = Column(BigInteger)
    file_type = Column(String(50))
    comment = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
