from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.role import Role
from app.schemas.user import UserResponse
from app.services.auth_service import get_current_user, require_permission

router = APIRouter()


@router.get("/", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_users")),
):
    result = await db.execute(select(User))
    return [UserResponse.model_validate(u) for u in result.scalars().all()]


@router.put("/{user_id}/role", response_model=UserResponse)
async def update_role(
    user_id: UUID,
    role_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_roles")),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    role_id = role_data.get("role_id")
    role_name = role_data.get("role")

    if role_id:
        role_result = await db.execute(select(Role).where(Role.id == role_id))
        role = role_result.scalar_one_or_none()
        if not role:
            raise HTTPException(status_code=404, detail="角色不存在")
        user.role = role.name
        user.role_id = role.id
    elif role_name:
        user.role = role_name
    else:
        raise HTTPException(status_code=400, detail="缺少 role 或 role_id 字段")

    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)
