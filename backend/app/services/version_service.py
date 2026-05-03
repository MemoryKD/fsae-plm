"""
版本服务 - 版本号解析、递增与零件号自动编号

版本号格式为 "大版本.小版本"（如 "A.1"、"B.3"）：
- 检入（checkin）时递增小版本：A.1 -> A.2
- 取消发布（unpublish）时递增大版本：A.2 -> B.1

零件号自动编号逻辑也在此模块中，通过模板+子系统+类型生成唯一编号。
"""
from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.part import Part
from app.models.version import Version
from app.models.template import PartNumberTemplate
from app.schemas.version import VersionResponse
from app.utils.file_storage import get_storage


def parse_version(version_str: str) -> tuple[str, int]:
    """解析版本号字符串，如 'A.1' -> ('A', 1)"""
    if not version_str:
        return ("A", 0)
    parts = version_str.split(".")
    if len(parts) == 2:
        return (parts[0], int(parts[1]))
    return ("A", 0)


def format_version(major: str, minor: int) -> str:
    """格式化版本号元组，如 ('A', 1) -> 'A.1'"""
    return f"{major}.{minor}"


def next_minor_version(current_version: str) -> str:
    """递增小版本号：A.1 -> A.2, B.3 -> B.4"""
    major, minor = parse_version(current_version)
    return format_version(major, minor + 1)


def next_major_version(current_version: str) -> str:
    """递增大版本号并重置小版本为 1：A.2 -> B.1, B.5 -> C.1"""
    major, _ = parse_version(current_version)
    # 大写字母递增：A->B->C...->Z
    new_major = chr(ord(major) + 1) if major else "B"
    return format_version(new_major, 1)


async def upload_version(
    part_id, version_number: str, comment: str, file: UploadFile,
    db: AsyncSession, user_id
) -> VersionResponse:
    """手动上传指定版本号的文件版本"""
    result = await db.execute(select(Part).where(Part.id == part_id))
    part = result.scalar_one_or_none()
    if not part:
        raise HTTPException(status_code=404, detail="零件不存在")

    if part.check_state == "检出" and str(part.checked_out_by) != str(user_id):
        raise HTTPException(status_code=403, detail="零件已被其他用户检出，无法上传版本")

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
    """列出零件的所有版本，按创建时间倒序"""
    result = await db.execute(
        select(Version).where(Version.part_id == part_id).order_by(Version.created_at.desc())
    )
    return [VersionResponse.model_validate(v) for v in result.scalars().all()]


async def get_version_file(part_id, version_id, db: AsyncSession):
    """获取指定版本的文件路径和文件名，用于版本文件下载"""
    result = await db.execute(
        select(Version).where(Version.id == version_id, Version.part_id == part_id)
    )
    version = result.scalar_one_or_none()
    if not version or not version.file_path:
        raise HTTPException(status_code=404, detail="版本不存在或没有文件")

    from app.models.part import Part
    part_result = await db.execute(select(Part).where(Part.id == part_id))
    part = part_result.scalar_one_or_none()
    ext = f".{version.file_type}" if version.file_type else ""
    filename = f"{part.part_number}_{version.version_number}{ext}" if part else f"version{ext}"

    return version.file_path, filename


# 默认类型代码映射，当模板未配置 type_codes 时使用
DEFAULT_TYPE_CODES = {
    "part": "PRT",
    "assembly": "ASM",
    "document": "DOC",
}


def _resolve_type_code(part_type: str, template_type_codes: dict | None) -> str:
    """根据零件类型和模板配置确定类型代码，模板自定义映射优先"""
    if template_type_codes:
        for key, code in template_type_codes.items():
            if key == part_type:
                return code
    return DEFAULT_TYPE_CODES.get(part_type, "PRT")


async def get_next_part_number(
    template_id, subsystem_code: str, db: AsyncSession, part_type: str = "part"
) -> dict:
    """获取该模板+子系统+类型组合下一个可用的零件号

    算法：查询数据库中同前缀的所有零件号，提取序号部分取最大值+1。
    返回包含 part_number、template_name、subsystem_code、type_code 的字典。
    """
    result = await db.execute(select(PartNumberTemplate).where(PartNumberTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    type_code = _resolve_type_code(part_type, template.type_codes)

    from app.services.number_engine import NumberEngine
    engine = NumberEngine.from_template(template)

    # 构建零件号前缀模式：PREFIX-TYPE_CODE-SUBSYSTEM-
    prefix = template.prefix or ""
    sep = template.separator or "-"
    parts = [p for p in [prefix, type_code, subsystem_code] if p]
    pattern_prefix = sep.join(parts) + sep if parts else ""

    # 查询所有匹配前缀的零件号，找出最大序号
    result = await db.execute(
        select(Part.part_number).where(Part.part_number.like(f"{pattern_prefix}%"))
    )
    existing = result.scalars().all()

    max_seq = 0
    for pn in existing:
        try:
            # 取最后一段作为序号，如 "FSAE-PRT-ENG-003" -> "003" -> 3
            seq_str = pn.split(sep)[-1]
            seq = int(seq_str)
            if seq > max_seq:
                max_seq = seq
        except (ValueError, IndexError):
            continue

    next_seq = max_seq + 1
    part_number = engine.generate(subsystem_code, next_seq, type_code)

    return {
        "part_number": part_number,
        "template_name": template.name,
        "subsystem_code": subsystem_code,
        "type_code": type_code,
    }
