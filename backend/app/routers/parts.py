from uuid import UUID
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.part import (
    PartCreate, PartResponse, NextPartNumberResponse, AutoPartCreate,
)
from app.services.part_service import (
    create_part, list_parts, get_part, checkout_part, checkin_part,
    publish_part, unpublish_part, auto_create_part, find_part_by_number,
    get_latest_version_file,
)
from app.services.version_service import get_next_part_number
from app.services.auth_service import get_current_user
from app.utils.file_storage import get_storage

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


@router.get("/next-number", response_model=NextPartNumberResponse)
async def get_next_number(
    template_id: UUID = Query(...),
    subsystem_code: str = Query(""),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_next_part_number(template_id, subsystem_code, db)


@router.post("/auto-create", response_model=PartResponse)
async def auto_create(
    name: str = Form(...),
    type: str = Form("part"),
    subsystem: str = Form(""),
    template_id: UUID = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await auto_create_part(name, type, subsystem, template_id, file, db, current_user.id)


@router.get("/check-number")
async def check_part_number(
    number: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """检查零件号是否已存在"""
    part = await find_part_by_number(number, db)
    return {"exists": part is not None, "part": part}


@router.get("/{part_id}", response_model=PartResponse)
async def get_part_detail(
    part_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_part(part_id, db)


@router.post("/{part_id}/checkout", response_model=PartResponse)
async def checkout(
    part_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await checkout_part(part_id, db, current_user.id)


@router.post("/{part_id}/checkin", response_model=PartResponse)
async def checkin(
    part_id: UUID,
    file: UploadFile = File(...),
    comment: str = Form(""),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await checkin_part(part_id, comment, file, db, current_user.id)


@router.post("/{part_id}/publish", response_model=PartResponse)
async def publish(
    part_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await publish_part(part_id, db, current_user.id)


@router.post("/{part_id}/unpublish", response_model=PartResponse)
async def unpublish(
    part_id: UUID,
    change_notice_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await unpublish_part(part_id, db, current_user.id, change_notice_id)


@router.get("/{part_id}/download")
async def download_file(
    part_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """下载零件最新版本文件"""
    file_path, filename = await get_latest_version_file(part_id, db)
    import os
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(file_path, filename=filename, media_type="application/octet-stream")


@router.post("/{part_id}/thumbnail")
async def upload_thumbnail(
    part_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传零件缩略图"""
    from app.models.part import Part
    from sqlalchemy import select

    result = await db.execute(select(Part).where(Part.id == part_id))
    part = result.scalar_one_or_none()
    if not part:
        raise HTTPException(status_code=404, detail="零件不存在")

    content = await file.read()
    if len(content) > 512000:
        raise HTTPException(status_code=400, detail="缩略图大小不能超过 500KB")

    storage = get_storage()
    thumb_path = await storage.save_thumbnail(str(part_id), content)
    part.thumbnail_path = thumb_path
    await db.commit()
    return {"message": "缩略图上传成功", "path": thumb_path}


@router.get("/{part_id}/thumbnail")
async def get_thumbnail(
    part_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取零件缩略图"""
    from app.models.part import Part
    from sqlalchemy import select

    result = await db.execute(select(Part).where(Part.id == part_id))
    part = result.scalar_one_or_none()
    if not part or not part.thumbnail_path:
        raise HTTPException(status_code=404, detail="缩略图不存在")

    import os
    if not os.path.exists(part.thumbnail_path):
        raise HTTPException(status_code=404, detail="缩略图文件不存在")

    return FileResponse(part.thumbnail_path, media_type="image/png")
