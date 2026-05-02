from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.part import Part
from app.models.version import Version
from app.models.template import PartNumberTemplate
from app.schemas.version import VersionResponse
from app.utils.file_storage import get_storage


def parse_version(version_str: str) -> tuple[str, int]:
    """解析版本号 'A.1' -> ('A', 1)"""
    if not version_str:
        return ("A", 0)
    parts = version_str.split(".")
    if len(parts) == 2:
        return (parts[0], int(parts[1]))
    return ("A", 0)


def format_version(major: str, minor: int) -> str:
    """格式化版本号 ('A', 1) -> 'A.1'"""
    return f"{major}.{minor}"


def next_minor_version(current_version: str) -> str:
    """递增小版本: A.1 -> A.2"""
    major, minor = parse_version(current_version)
    return format_version(major, minor + 1)


def next_major_version(current_version: str) -> str:
    """递增大版本: A.2 -> B.1"""
    major, _ = parse_version(current_version)
    new_major = chr(ord(major) + 1) if major else "B"
    return format_version(new_major, 1)


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


async def get_next_part_number(template_id, subsystem_code: str, db: AsyncSession) -> dict:
    """获取该模板+子系统下一个可用零件号"""
    result = await db.execute(select(PartNumberTemplate).where(PartNumberTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    from app.services.number_engine import NumberEngine
    engine = NumberEngine.from_template(template)

    prefix = template.prefix or ""
    sep = template.separator or "-"
    pattern_prefix = f"{prefix}{sep}{subsystem_code}{sep}" if prefix else f"{subsystem_code}{sep}"

    result = await db.execute(
        select(Part.part_number).where(Part.part_number.like(f"{pattern_prefix}%"))
    )
    existing = result.scalars().all()

    max_seq = 0
    for pn in existing:
        try:
            seq_str = pn.split(sep)[-1]
            seq = int(seq_str)
            if seq > max_seq:
                max_seq = seq
        except (ValueError, IndexError):
            continue

    next_seq = max_seq + 1
    part_number = engine.generate(subsystem_code, next_seq)

    return {
        "part_number": part_number,
        "template_name": template.name,
        "subsystem_code": subsystem_code,
    }
