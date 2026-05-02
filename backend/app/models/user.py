"""
用户模型 - 系统用户与注册审批

支持注册审批流程：新用户注册后状态为 pending，需管理员审批后方可登录。
角色通过 role_id 外键关联 roles 表，旧 role 字段仅用于数据迁移兼容。
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from app.utils.types import PortableUUID as UUID

from app.database import Base


class User(Base):
    """系统用户，包含认证信息、团队归属和审批状态"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    # 已废弃：旧版角色字段，保留用于数据迁移，新逻辑使用 role_id
    role = Column(String(20))
    # 关联角色表，通过 Role.permissions 获取权限列表
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=True)
    team = Column(String(50))
    full_name = Column(String(100))
    department = Column(String(100))
    join_year = Column(String(4))
    phone = Column(String(20))
    # 注册审批状态：pending（待审批）、approved（已批准）、rejected（已拒绝）
    status = Column(String(20), default="approved")
    created_at = Column(DateTime, default=datetime.utcnow)
