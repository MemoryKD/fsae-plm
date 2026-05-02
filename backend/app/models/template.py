"""
编号模板模型 - 零件号自动生成规则配置

编号模板定义零件号的生成格式，由编号引擎（number_engine）使用。
示例格式：PREFIX-TYPE_CODE-SUBSYSTEM-001
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from app.utils.types import PortableUUID as UUID, PortableJSON as JSONB

from app.database import Base


class PartNumberTemplate(Base):
    """零件号模板，配置前缀、分隔符、序号位数等编号规则"""

    __tablename__ = "part_number_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # 模板名称，如"2026赛季零件编号"
    name = Column(String(100), nullable=False)
    # 编号前缀，如"FSAE"
    prefix = Column(String(20))
    # 各段之间的分隔符，默认 "-"
    separator = Column(String(5), default="-")
    # 序号的零填充位数，如 3 表示 001、002...
    digit_count = Column(Integer, default=3)
    # 子系统代码映射，如 {"动力": "ENG", "底盘": "CHS"}
    subsystem_codes = Column(JSONB, default=dict)
    # 类型代码映射，如 {"part": "PRT", "assembly": "ASM"}
    type_codes = Column(JSONB, default=dict)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
