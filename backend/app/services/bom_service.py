"""
BOM（物料清单）服务 - 装配体子件管理与 Excel 导出

提供 BOM 的增删查和导出功能，支持：
- 添加/删除 BOM 条目（装配体与子件的关联）
- 查询装配体的 BOM 列表
- 导出 BOM 为 Excel 文件
- 获取装配体关联的所有零件（供级联检出/检入使用）
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from openpyxl import Workbook

from app.models.bom import BomItem
from app.models.part import Part
from app.schemas.bom import BomItemCreate, BomItemResponse


async def add_bom_item(assembly_id, data: BomItemCreate, db: AsyncSession) -> BomItemResponse:
    """向装配体添加一个 BOM 子件条目"""
    item = BomItem(assembly_id=assembly_id, **data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return BomItemResponse.model_validate(item)


async def get_bom(assembly_id, db: AsyncSession) -> list[BomItemResponse]:
    """获取装配体的完整 BOM 列表，按层级排序"""
    result = await db.execute(
        select(BomItem).where(BomItem.assembly_id == assembly_id).order_by(BomItem.level)
    )
    return [BomItemResponse.model_validate(i) for i in result.scalars().all()]


async def export_bom_excel(assembly_id, db: AsyncSession) -> bytes:
    """将装配体的 BOM 导出为 Excel 文件，返回字节流"""
    items = await get_bom(assembly_id, db)
    wb = Workbook()
    ws = wb.active
    ws.title = "BOM"
    # 表头：序号、层级、零件编号、零件名称、版本号、数量、类型
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


async def get_assembly_parts(assembly_id, db: AsyncSession) -> list:
    """获取装配体下所有直接关联的零件对象（用于级联检出/检入）"""
    result = await db.execute(
        select(Part).join(BomItem, BomItem.part_id == Part.id)
        .where(BomItem.assembly_id == assembly_id)
    )
    return list(result.scalars().all())


async def remove_bom_item(bom_item_id, db: AsyncSession):
    """删除指定的 BOM 条目"""
    result = await db.execute(select(BomItem).where(BomItem.id == bom_item_id))
    item = result.scalar_one_or_none()
    if not item:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="BOM 项不存在")
    await db.delete(item)
    await db.commit()
    return {"message": "已删除"}
