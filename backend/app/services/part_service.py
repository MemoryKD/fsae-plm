from fastapi import HTTPException, UploadFile
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.part import Part
from app.models.user import User
from app.schemas.part import PartCreate, PartResponse
from app.services.version_service import next_minor_version, next_major_version
from app.utils.file_storage import get_storage


async def create_part(data: PartCreate, db: AsyncSession, user_id) -> PartResponse:
    result = await db.execute(select(Part).where(Part.part_number == data.part_number))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="零件编号已存在")

    part = Part(**data.model_dump(), created_by=user_id, current_version="A.1")
    db.add(part)
    await db.commit()
    await db.refresh(part)
    return PartResponse.model_validate(part)


async def auto_create_part(
    name: str, part_type: str, subsystem: str, template_id,
    file: UploadFile, db: AsyncSession, user_id
) -> PartResponse:
    """自动创建零件：生成零件号，重命名文件，上传"""
    from app.services.version_service import get_next_part_number

    next_info = await get_next_part_number(template_id, subsystem or "", db)
    part_number = next_info["part_number"]

    part = Part(
        part_number=part_number,
        name=name,
        type=part_type,
        subsystem=subsystem,
        template_id=template_id,
        current_version="A.1",
        lifecycle_state="工作中",
        check_state="检入",
        created_by=user_id,
    )
    db.add(part)
    await db.flush()

    content = await file.read()
    storage = get_storage()
    original_name = file.filename or "file"
    ext = original_name.rsplit(".", 1)[-1] if "." in original_name else ""
    new_filename = f"{part_number}.{ext}" if ext else part_number
    file_path, file_size = await storage.save(content, new_filename)

    from app.models.version import Version
    version = Version(
        part_id=part.id,
        version_number="A.1",
        file_path=file_path,
        file_size=file_size,
        file_type=ext,
        comment="初始创建",
        created_by=user_id,
    )
    db.add(version)
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


async def checkout_part(part_id, db: AsyncSession, user_id) -> PartResponse:
    """检出零件"""
    result = await db.execute(select(Part).where(Part.id == part_id))
    part = result.scalar_one_or_none()
    if not part:
        raise HTTPException(status_code=404, detail="零件不存在")

    if part.check_state == "检出":
        user_result = await db.execute(select(User).where(User.id == part.checked_out_by))
        user = user_result.scalar_one_or_none()
        username = user.username if user else "未知用户"
        raise HTTPException(
            status_code=409,
            detail=f"零件已被 {username} 检出，无法重复检出"
        )

    part.check_state = "检出"
    part.checked_out_by = user_id
    await db.commit()
    await db.refresh(part)
    return PartResponse.model_validate(part)


async def checkin_part(
    part_id, comment: str, file: UploadFile,
    db: AsyncSession, user_id
) -> PartResponse:
    """检入零件：上传文件，递增小版本"""
    result = await db.execute(select(Part).where(Part.id == part_id))
    part = result.scalar_one_or_none()
    if not part:
        raise HTTPException(status_code=404, detail="零件不存在")

    if part.check_state != "检出":
        raise HTTPException(status_code=400, detail="零件未检出，无法检入")

    new_version = next_minor_version(part.current_version or "A.0")

    content = await file.read()
    storage = get_storage()
    file_path, file_size = await storage.save(content, file.filename)

    from app.models.version import Version
    version = Version(
        part_id=part_id,
        version_number=new_version,
        file_path=file_path,
        file_size=file_size,
        file_type=file.filename.split(".")[-1] if file.filename else None,
        comment=comment,
        created_by=user_id,
    )
    db.add(version)

    part.current_version = new_version
    part.check_state = "检入"
    part.checked_out_by = None

    await db.commit()
    await db.refresh(part)
    return PartResponse.model_validate(part)


async def publish_part(part_id, db: AsyncSession, user_id) -> PartResponse:
    """发布零件"""
    result = await db.execute(select(Part).where(Part.id == part_id))
    part = result.scalar_one_or_none()
    if not part:
        raise HTTPException(status_code=404, detail="零件不存在")

    if part.check_state == "检出":
        raise HTTPException(status_code=400, detail="零件正在检出中，无法发布")

    part.lifecycle_state = "已发布"
    part.check_state = "检入"
    await db.commit()
    await db.refresh(part)
    return PartResponse.model_validate(part)


async def unpublish_part(part_id, db: AsyncSession, user_id, change_notice_id=None) -> PartResponse:
    """取消发布：需要已批准的更改通告，回到工作中，递增大版本"""
    from app.models.change_notice import ChangeNotice

    result = await db.execute(select(Part).where(Part.id == part_id))
    part = result.scalar_one_or_none()
    if not part:
        raise HTTPException(status_code=404, detail="零件不存在")

    if part.lifecycle_state != "已发布":
        raise HTTPException(status_code=400, detail="零件未发布，无法取消发布")

    if not change_notice_id:
        raise HTTPException(status_code=400, detail="取消发布需要提供更改通告编号")

    cn_result = await db.execute(select(ChangeNotice).where(ChangeNotice.id == change_notice_id))
    cn = cn_result.scalar_one_or_none()
    if not cn or cn.part_id != part_id:
        raise HTTPException(status_code=400, detail="更改通告不存在或不属于该零件")
    if cn.status != "已批准":
        raise HTTPException(status_code=400, detail="更改通告未经批准，无法取消发布")

    cn.status = "已完成"
    new_version = next_major_version(part.current_version or "A.1")
    part.lifecycle_state = "工作中"
    part.check_state = "检入"
    part.current_version = new_version
    await db.commit()
    await db.refresh(part)
    return PartResponse.model_validate(part)


async def find_part_by_number(part_number: str, db: AsyncSession) -> PartResponse | None:
    """根据零件号查找零件"""
    result = await db.execute(select(Part).where(Part.part_number == part_number))
    part = result.scalar_one_or_none()
    if part:
        return PartResponse.model_validate(part)
    return None


async def get_latest_version_file(part_id, db: AsyncSession):
    """获取零件最新版本的文件路径和文件名"""
    from app.models.version import Version
    from sqlalchemy import desc

    result = await db.execute(
        select(Version)
        .where(Version.part_id == part_id)
        .order_by(desc(Version.created_at))
        .limit(1)
    )
    version = result.scalar_one_or_none()
    if not version or not version.file_path:
        raise HTTPException(status_code=404, detail="该零件没有可下载的文件")

    # 获取零件号用于文件名
    part_result = await db.execute(select(Part).where(Part.id == part_id))
    part = part_result.scalar_one_or_none()
    ext = f".{version.file_type}" if version.file_type else ""
    filename = f"{part.part_number}_{version.version_number}{ext}" if part else f"file{ext}"

    return version.file_path, filename
