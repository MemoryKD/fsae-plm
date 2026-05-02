from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.version import VersionResponse
from app.services.version_service import upload_version, list_versions, get_version_file
from app.services.auth_service import get_current_user

router = APIRouter()


@router.get("/{part_id}/versions", response_model=list[VersionResponse])
async def get_versions(
    part_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await list_versions(part_id, db)


@router.post("/{part_id}/versions", response_model=VersionResponse)
async def create_version(
    part_id: UUID,
    version_number: str = Form(...),
    comment: str = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await upload_version(part_id, version_number, comment, file, db, current_user.id)


@router.get("/{part_id}/versions/{version_id}/download")
async def download_version(
    part_id: UUID,
    version_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """下载指定版本的文件"""
    file_path, filename = await get_version_file(part_id, version_id, db)
    import os
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(file_path, filename=filename, media_type="application/octet-stream")
