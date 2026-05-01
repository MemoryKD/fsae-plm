from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from app.utils.security import hash_password, verify_password, create_access_token, decode_access_token
from app.database import get_db

security = HTTPBearer()


async def register(user_data: UserCreate, db: AsyncSession) -> UserResponse:
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        team=user_data.team,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


async def login(login_data: UserLogin, db: AsyncSession) -> TokenResponse:
    result = await db.execute(select(User).where(User.username == login_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_access_token({"sub": str(user.id), "username": user.username, "role": user.role})
    return TokenResponse(access_token=token)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")

    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user
