"""
BOM（物料清单）模型 - 装配体与子件的关联关系

BOM 表达"哪个装配体包含哪些零件"的层级关系。
assembly_id 指向父装配体，part_id 指向被包含的子件。
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from app.utils.types import PortableUUID as UUID

from app.database import Base


class BomItem(Base):
    """BOM 条目，描述装配体与子件之间的包含关系"""

    __tablename__ = "bom_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # 父装配体 ID（类型为 assembly 的零件）
    assembly_id = Column(UUID(as_uuid=True), ForeignKey("parts.id"), nullable=False, index=True)
    # 被包含的子件 ID
    part_id = Column(UUID(as_uuid=True), ForeignKey("parts.id"), nullable=False)
    # 该子件在装配体中的使用数量
    quantity = Column(Integer, default=1)
    # BOM 层级深度，0 表示直接子件
    level = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
