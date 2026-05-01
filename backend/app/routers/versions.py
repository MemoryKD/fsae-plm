from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.version import VersionResponse
from app.services.version_service import upload_version, list_versions
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
