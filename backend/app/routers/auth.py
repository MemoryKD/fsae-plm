"""
认证路由 - 用户注册、登录、审批相关 API 端点

端点列表：
- POST /register   - 用户注册（状态为 pending）
- POST /login      - 用户登录（返回 JWT 令牌）
- GET  /me         - 获取当前用户信息和权限
- GET  /pending-users - 列出待审批用户（需 manage_users 权限）
- POST /approve/{user_id} - 批准用户注册
- POST /reject/{user_id}  - 拒绝用户注册
"""
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from app.services.auth_service import register, login, get_current_user, require_permission, list_pending_users, approve_user, reject_user

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """用户注册接口，新用户默认待审批状态"""
    return await register(user_data, db)


@router.post("/login", response_model=TokenResponse)
async def login_user(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """用户登录接口，返回 JWT 令牌和权限列表"""
    return await login(login_data, db)


@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前登录用户的详细信息和权限列表"""
    from app.services.auth_service import get_user_permissions
    permissions = await get_user_permissions(current_user, db)
    user_data = UserResponse.model_validate(current_user).model_dump()
    user_data["permissions"] = permissions
    return user_data


@router.get("/pending-users")
async def get_pending_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_users")),
):
    """列出所有待审批用户（需要 manage_users 权限）"""
    return await list_pending_users(db)


@router.post("/approve/{user_id}", response_model=UserResponse)
async def approve(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_users")),
):
    """批准用户注册（需要 manage_users 权限）"""
    return await approve_user(user_id, db)


@router.post("/reject/{user_id}", response_model=UserResponse)
async def reject(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_users")),
):
    """拒绝用户注册（需要 manage_users 权限）"""
    return await reject_user(user_id, db)
