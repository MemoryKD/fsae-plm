"""
更改通告模型 - 已发布零件的变更管理

已发布的零件处于只读状态，任何修改都需要通过更改通告流程：
1. 创建更改通告并说明变更原因
2. 管理员审批通过
3. 使用"取消发布"操作将零件退回工作中状态（递增大版本号）
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from app.utils.types import PortableUUID as UUID

from app.database import Base


class ChangeNotice(Base):
    """更改通告，记录已发布零件变更的原因、审批和执行状态"""

    __tablename__ = "change_notices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # 通告编号，全局唯一
    notice_number = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    # 变更详细描述
    description = Column(Text)
    # 变更原因（必填）
    reason = Column(Text, nullable=False)
    # 关联的目标零件
    part_id = Column(UUID(as_uuid=True), ForeignKey("parts.id"), nullable=False, index=True)
    # 审批状态：待审批 → 已批准/已拒绝 → 已完成（执行取消发布后）
    status = Column(String(20), default="待审批")
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    # 审批人（批准或拒绝时记录）
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
