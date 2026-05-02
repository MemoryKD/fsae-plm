"""
零件模型 - FSAE-PLM 系统的核心数据模型

定义零件（Part）的数据库结构，包含以下关键业务字段：
- 生命周期状态（工作中/已发布）
- 检入/检出状态（支持并发控制）
- 分支与衍生关系（支持零件变体管理）
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from app.utils.types import PortableUUID as UUID

from app.database import Base


class Part(Base):
    """零件模型，承载零件编号、版本、生命周期等全部元数据"""

    __tablename__ = "parts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # 零件编号，全局唯一，由编号模板引擎生成
    part_number = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    # 零件类型：part（零件）、assembly（装配体）、document（文档）
    type = Column(String(20), nullable=False)
    # 所属子系统，如动力、底盘、车身等
    subsystem = Column(String(50))
    # 关联的编号模板，用于自动生成零件号
    template_id = Column(UUID(as_uuid=True), ForeignKey("part_number_templates.id"), nullable=True)
    # 当前版本号，格式为 "大版本.小版本"，如 "A.1"
    current_version = Column(String(10))
    # 工作流状态，如"设计中"、"审核中"等
    workflow_state = Column(String(50), default="设计中")
    # 生命周期状态：工作中（可编辑）/ 已发布（只读，需更改通告才能修改）
    lifecycle_state = Column(String(20), default="工作中")
    # 检入/检出状态，实现并发编辑控制：检入=空闲可编辑，检出=锁定中
    check_state = Column(String(20), default="检入")
    # 当前检出者，仅在 check_state="检出" 时有值
    checked_out_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    # 缩略图文件路径
    thumbnail_path = Column(String(500), nullable=True)
    # 衍生来源：记录该零件从哪个零件分支而来（用于分支管理）
    derived_from_id = Column(UUID(as_uuid=True), ForeignKey("parts.id"), nullable=True)
    # 分支名称，如 "V2改型"、"轻量化版"
    branch_name = Column(String(100), nullable=True)
    branch_created_at = Column(DateTime, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
