"""
认证与授权服务 - 用户注册、登录、权限校验

业务流程：
1. 用户注册后状态为 pending（待审批）
2. 管理员审批通过后状态变为 approved，用户方可登录
3. 登录时返回 JWT 令牌和权限列表
4. 权限校验基于 RBAC：admin 拥有全部权限，其他用户通过 role_id 查 roles 表
"""
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.role import Role, ALL_PERMISSIONS
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from app.utils.security import hash_password, verify_password, create_access_token, decode_access_token
from app.database import get_db

# HTTP Bearer 认证方案，从请求头提取 JWT 令牌
security = HTTPBearer()


async def register(user_data: UserCreate, db: AsyncSession) -> UserResponse:
    """用户注册，新用户默认为 viewer 角色、pending 状态（需管理员审批）"""
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 新注册用户默认分配 viewer 角色
    role_result = await db.execute(select(Role).where(Role.name == "viewer"))
    default_role = role_result.scalar_one_or_none()

    user = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name,
        department=user_data.department,
        join_year=user_data.join_year,
        phone=user_data.phone,
        role="viewer",
        role_id=default_role.id if default_role else None,
        status="pending",  # 注册后需管理员审批
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


async def login(login_data: UserLogin, db: AsyncSession) -> TokenResponse:
    """用户登录：校验密码和审批状态，返回 JWT 令牌和权限列表"""
    result = await db.execute(select(User).where(User.username == login_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    # 未审批或已拒绝的用户无法登录
    if user.status == "pending":
        raise HTTPException(status_code=403, detail="账号正在等待审批，请联系管理员")
    if user.status == "rejected":
        raise HTTPException(status_code=403, detail="账号已被拒绝")

    permissions = await get_user_permissions(user, db)
    token = create_access_token({"sub": str(user.id), "username": user.username, "role": user.role or ""})
    return TokenResponse(access_token=token, permissions=permissions)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """从 JWT 令牌解析当前登录用户，用作 FastAPI 依赖注入"""
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")

    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


async def get_user_permissions(user: User, db: AsyncSession) -> list[str]:
    """获取用户的权限列表。admin 角色直接返回全部权限。"""
    if user.role == "admin":
        return list(ALL_PERMISSIONS)
    if not user.role_id:
        return []
    result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = result.scalar_one_or_none()
    return role.permissions if role else []


def require_permission(permission: str):
    """权限校验装饰器工厂，返回一个 FastAPI 依赖函数，检查用户是否拥有指定权限"""
    async def checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        # admin 角色跳过权限检查
        if current_user.role == "admin":
            return current_user
        perms = await get_user_permissions(current_user, db)
        if permission not in perms:
            raise HTTPException(status_code=403, detail=f"权限不足: 需要 {permission}")
        return current_user
    return checker


async def list_pending_users(db: AsyncSession) -> list[UserResponse]:
    """列出所有待审批用户，按注册时间倒序"""
    result = await db.execute(
        select(User).where(User.status == "pending").order_by(User.created_at.desc())
    )
    return [UserResponse.model_validate(u) for u in result.scalars().all()]


async def approve_user(user_id, db: AsyncSession) -> UserResponse:
    """批准用户注册，状态从 pending 变为 approved"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.status != "pending":
        raise HTTPException(status_code=400, detail="用户不在待审批状态")
    user.status = "approved"
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


async def reject_user(user_id, db: AsyncSession) -> UserResponse:
    """拒绝用户注册，状态从 pending 变为 rejected"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.status != "pending":
        raise HTTPException(status_code=400, detail="用户不在待审批状态")
    user.status = "rejected"
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)
