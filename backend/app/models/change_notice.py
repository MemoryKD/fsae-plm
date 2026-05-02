import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from app.utils.types import PortableUUID as UUID

from app.database import Base


class ChangeNotice(Base):
    """更改通告 - 用于管理已发布零件的变更"""
    __tablename__ = "change_notices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    notice_number = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    reason = Column(Text, nullable=False)
    part_id = Column(UUID(as_uuid=True), ForeignKey("parts.id"), nullable=False, index=True)
    status = Column(String(20), default="待审批")  # 待审批 / 已批准 / 已拒绝 / 已完成
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
