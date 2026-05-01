from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.part import Part
from app.models.version import Version
from app.schemas.version import VersionResponse
from app.utils.file_storage import get_storage


async def upload_version(
    part_id, version_number: str, comment: str, file: UploadFile,
    db: AsyncSession, user_id
) -> VersionResponse:
    result = await db.execute(select(Part).where(Part.id == part_id))
    part = result.scalar_one_or_none()
    if not part:
        raise HTTPException(status_code=404, detail="零件不存在")

    content = await file.read()
    storage = get_storage()
    file_path, file_size = await storage.save(content, file.filename)

    version = Version(
        part_id=part_id, version_number=version_number,
        file_path=file_path, file_size=file_size,
        file_type=file.filename.split(".")[-1] if file.filename else None,
        comment=comment, created_by=user_id,
    )
    db.add(version)
    part.current_version = version_number
    await db.commit()
    await db.refresh(version)
    return VersionResponse.model_validate(version)


async def list_versions(part_id, db: AsyncSession) -> list[VersionResponse]:
    result = await db.execute(
        select(Version).where(Version.part_id == part_id).order_by(Version.created_at.desc())
    )
    return [VersionResponse.model_validate(v) for v in result.scalars().all()]
