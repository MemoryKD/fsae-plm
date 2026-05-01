from fastapi import HTTPException
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.part import Part
from app.schemas.part import PartCreate, PartResponse


async def create_part(data: PartCreate, db: AsyncSession, user_id) -> PartResponse:
    result = await db.execute(select(Part).where(Part.part_number == data.part_number))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="零件编号已存在")

    part = Part(**data.model_dump(), created_by=user_id)
    db.add(part)
    await db.commit()
    await db.refresh(part)
    return PartResponse.model_validate(part)


async def list_parts(db: AsyncSession, search: str | None = None) -> list[PartResponse]:
    query = select(Part)
    if search:
        query = query.where(
            or_(Part.part_number.ilike(f"%{search}%"), Part.name.ilike(f"%{search}%"), Part.subsystem.ilike(f"%{search}%"))
        )
    query = query.order_by(Part.created_at.desc())
    result = await db.execute(query)
    return [PartResponse.model_validate(p) for p in result.scalars().all()]


async def get_part(part_id, db: AsyncSession) -> PartResponse:
    result = await db.execute(select(Part).where(Part.id == part_id))
    part = result.scalar_one_or_none()
    if not part:
        raise HTTPException(status_code=404, detail="零件不存在")
    return PartResponse.model_validate(part)
