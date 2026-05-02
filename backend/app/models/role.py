"""
角色与权限模型 - RBAC 权限管理

系统采用基于角色的访问控制（RBAC），预置四种角色：
- admin（管理员）：全部权限
- manager（经理）：除角色管理和封禁用户外的全部权限
- designer（设计师）：零件的增删改查和检入检出
- viewer（查看者）：仅查看

角色的 is_system="1" 表示系统预置角色，不可删除。
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from app.utils.types import PortableUUID as UUID, PortableJSON as JSONB

from app.database import Base

# 系统全部权限列表，用于权限校验和角色配置
ALL_PERMISSIONS = [
    "create_parts", "edit_parts", "checkout_parts", "checkin_parts", "view_parts",
    "publish_parts", "unpublish_parts", "delete_parts", "manage_bom",
    "manage_users", "manage_templates", "manage_knowledge", "manage_workflows",
    "approve_change_notices", "ban_users", "manage_roles",
]

# 系统预置角色定义，首次启动时由 database._seed_roles() 写入数据库
DEFAULT_ROLES = [
    {
        "name": "admin",
        "display_name": "管理员",
        "permissions": list(ALL_PERMISSIONS),
        "is_system": "1",
    },
    {
        "name": "manager",
        "display_name": "经理",
        # 经理角色排除：管理角色、封禁用户
        "permissions": [p for p in ALL_PERMISSIONS if p not in ("manage_roles", "ban_users")],
        "is_system": "1",
    },
    {
        "name": "designer",
        "display_name": "设计师",
        "permissions": ["create_parts", "edit_parts", "checkout_parts", "checkin_parts", "view_parts"],
        "is_system": "1",
    },
    {
        "name": "viewer",
        "display_name": "查看者",
        "permissions": ["view_parts"],
        "is_system": "1",
    },
]


class Role(Base):
    """角色模型，存储角色名称和对应的权限列表（JSON 数组）"""

    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # 角色标识名，如 "admin"、"designer"
    name = Column(String(50), unique=True, nullable=False)
    # 角色显示名称，如 "管理员"、"设计师"
    display_name = Column(String(100), nullable=False)
    # 权限列表，存储为 JSON 数组
    permissions = Column(JSONB, nullable=False, default=list)
    # 是否系统预置角色："1"=系统角色（不可删除），"0"=用户自定义
    is_system = Column(String(1), default="0")
    created_at = Column(DateTime, default=datetime.utcnow)
