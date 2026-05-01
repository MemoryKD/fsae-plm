from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.part import PartCreate, PartResponse
from app.services.part_service import create_part, list_parts, get_part
from app.services.auth_service import get_current_user

router = APIRouter()


@router.get("/", response_model=list[PartResponse])
async def get_parts(
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await list_parts(db, search)


@router.post("/", response_model=PartResponse)
async def create_new_part(
    data: PartCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await create_part(data, db, current_user.id)


@router.get("/{part_id}", response_model=PartResponse)
async def get_part_detail(
    part_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_part(part_id, db)
