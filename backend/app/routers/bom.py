from uuid import UUID
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from io import BytesIO

from app.database import get_db
from app.models.user import User
from app.schemas.bom import BomItemCreate, BomItemResponse
from app.services.bom_service import add_bom_item, get_bom, export_bom_excel
from app.services.auth_service import get_current_user

router = APIRouter()


@router.get("/{part_id}/bom", response_model=list[BomItemResponse])
async def get_part_bom(
    part_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_bom(part_id, db)


@router.post("/{part_id}/bom", response_model=BomItemResponse)
async def add_bom(
    part_id: UUID,
    data: BomItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await add_bom_item(part_id, data, db)


@router.get("/{part_id}/bom/export")
async def export_bom(
    part_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = await export_bom_excel(part_id, db)
    return StreamingResponse(
        BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=bom.xlsx"},
    )
