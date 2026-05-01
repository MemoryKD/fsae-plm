from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from openpyxl import Workbook

from app.models.bom import BomItem
from app.models.part import Part
from app.schemas.bom import BomItemCreate, BomItemResponse


async def add_bom_item(assembly_id, data: BomItemCreate, db: AsyncSession) -> BomItemResponse:
    item = BomItem(assembly_id=assembly_id, **data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return BomItemResponse.model_validate(item)


async def get_bom(assembly_id, db: AsyncSession) -> list[BomItemResponse]:
    result = await db.execute(
        select(BomItem).where(BomItem.assembly_id == assembly_id).order_by(BomItem.level)
    )
    return [BomItemResponse.model_validate(i) for i in result.scalars().all()]


async def export_bom_excel(assembly_id, db: AsyncSession) -> bytes:
    items = await get_bom(assembly_id, db)
    wb = Workbook()
    ws = wb.active
    ws.title = "BOM"
    ws.append(["序号", "层级", "零件编号", "零件名称", "版本号", "数量", "类型"])

    for idx, item in enumerate(items, 1):
        result = await db.execute(select(Part).where(Part.id == item.part_id))
        part = result.scalar_one_or_none()
        if part:
            ws.append([idx, item.level, part.part_number, part.name, part.current_version or "N/A", item.quantity, part.type])

    from io import BytesIO
    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
