from uuid import UUID
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from io import BytesIO

from app.database import get_db
from app.models.user import User
from app.schemas.bom import BomItemCreate, BomItemResponse
from app.services.bom_service import add_bom_item, get_bom, export_bom_excel, remove_bom_item, get_assembly_parts
from app.services.auth_service import get_current_user, require_permission

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
    current_user: User = Depends(require_permission("manage_bom")),
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


@router.delete("/{part_id}/bom/{bom_item_id}")
async def delete_bom_item(
    part_id: UUID,
    bom_item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_bom")),
):
    return await remove_bom_item(bom_item_id, db)


@router.get("/{part_id}/bom/parts", response_model=list)
async def get_bom_parts(
    part_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取装配体下所有关联零件"""
    from app.schemas.part import PartResponse
    parts = await get_assembly_parts(part_id, db)
    return [PartResponse.model_validate(p) for p in parts]
