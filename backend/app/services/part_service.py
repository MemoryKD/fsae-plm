"""
零件核心业务服务 - 实现零件全生命周期管理

包含以下核心业务流程：
- 创建零件（手动/模板自动编号/带文件自动创建）
- 检入/检出（并发编辑控制，装配体级联锁定）
- 发布/取消发布（需更改通告审批）
- 分支管理（从现有零件派生变体）
- 衍生链查询（追溯零件来源）
- 删除（级联清理版本和 BOM 引用）
"""
from datetime import datetime
from fastapi import HTTPException, UploadFile
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.part import Part
from app.models.user import User
from app.schemas.part import PartCreate, PartResponse
from app.services.version_service import next_minor_version, next_major_version
from app.utils.file_storage import get_storage


async def create_part(data: PartCreate, db: AsyncSession, user_id) -> PartResponse:
    """手动创建零件（零件号由前端指定）"""
    result = await db.execute(select(Part).where(Part.part_number == data.part_number))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="零件编号已存在")

    part = Part(**data.model_dump(), created_by=user_id, current_version="A.1")
    db.add(part)
    await db.commit()
    await db.refresh(part)
    return PartResponse.model_validate(part)


async def create_part_with_template(
    name: str, part_type: str, subsystem: str, template_id,
    db: AsyncSession, user_id
) -> PartResponse:
    """使用模板自动编号创建零件（不需要文件）"""
    from app.services.version_service import get_next_part_number

    next_info = await get_next_part_number(template_id, subsystem or "", db, part_type)
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
    await db.commit()
    await db.refresh(part)
    return PartResponse.model_validate(part)


async def auto_create_part(
    name: str, part_type: str, subsystem: str, template_id,
    file: UploadFile, db: AsyncSession, user_id
) -> PartResponse:
    """自动创建零件：生成零件号，重命名文件，上传并创建初始版本"""
    from app.services.version_service import get_next_part_number

    next_info = await get_next_part_number(template_id, subsystem or "", db, part_type)
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
    await db.flush()  # 先 flush 获取 part.id，再创建关联的版本记录

    content = await file.read()
    storage = get_storage()
    original_name = file.filename or "file"
    ext = original_name.rsplit(".", 1)[-1] if "." in original_name else ""
    # 用零件号重命名文件，便于识别
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
    """列出零件，支持按零件号、名称、子系统模糊搜索"""
    query = select(Part)
    if search:
        query = query.where(
            or_(Part.part_number.ilike(f"%{search}%"), Part.name.ilike(f"%{search}%"), Part.subsystem.ilike(f"%{search}%"))
        )
    query = query.order_by(Part.created_at.desc())
    result = await db.execute(query)
    return [PartResponse.model_validate(p) for p in result.scalars().all()]


async def get_part(part_id, db: AsyncSession) -> PartResponse:
    """获取单个零件详情"""
    result = await db.execute(select(Part).where(Part.id == part_id))
    part = result.scalar_one_or_none()
    if not part:
        raise HTTPException(status_code=404, detail="零件不存在")
    return PartResponse.model_validate(part)


async def checkout_part(part_id, db: AsyncSession, user_id) -> PartResponse:
    """检出零件，锁定为当前用户编辑。装配体类型会级联检出所有子件。"""
    result = await db.execute(select(Part).where(Part.id == part_id))
    part = result.scalar_one_or_none()
    if not part:
        raise HTTPException(status_code=404, detail="零件不存在")

    # 检查是否已被他人检出
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

    # 装配体级联检出：确保子件也处于锁定状态，防止其他用户同时修改
    if part.type == "assembly":
        from app.services.bom_service import get_assembly_parts
        bom_parts = await get_assembly_parts(part_id, db)
        for bp in bom_parts:
            if bp.check_state == "检入":
                bp.check_state = "检出"
                bp.checked_out_by = user_id

    await db.commit()
    await db.refresh(part)
    return PartResponse.model_validate(part)


async def checkin_part(
    part_id, comment: str, file: UploadFile,
    db: AsyncSession, user_id
) -> PartResponse:
    """检入零件：上传新文件，自动递增小版本号（A.1 -> A.2）"""
    result = await db.execute(select(Part).where(Part.id == part_id))
    part = result.scalar_one_or_none()
    if not part:
        raise HTTPException(status_code=404, detail="零件不存在")

    if part.check_state != "检出":
        raise HTTPException(status_code=400, detail="零件未检出，无法检入")

    # 装配体检入前，校验所有子件必须已检入（保证数据一致性）
    if part.type == "assembly":
        from app.services.bom_service import get_assembly_parts
        bom_parts = await get_assembly_parts(part_id, db)
        unchecked = [bp for bp in bom_parts if bp.check_state == "检出"]
        if unchecked:
            names = ", ".join(bp.part_number for bp in unchecked)
            raise HTTPException(
                status_code=400,
                detail=f"关联零件未检入，无法检入装配体: {names}"
            )

    # 检入递增小版本号：A.1 -> A.2, A.2 -> A.3 ...
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

    # 异步生成 3D 预览（非关键路径，失败不影响检入）
    try:
        from app.services.preview_service import convert_to_gltf
        await convert_to_gltf(file_path, str(part_id))
    except Exception:
        pass

    return PartResponse.model_validate(part)


async def publish_part(part_id, db: AsyncSession, user_id) -> PartResponse:
    """发布零件：将生命周期状态设为"已发布"，此后零件变为只读"""
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
    """取消发布：需要已批准的更改通告，回到工作中状态，大版本号递增（A->B）"""
    from app.models.change_notice import ChangeNotice

    result = await db.execute(select(Part).where(Part.id == part_id))
    part = result.scalar_one_or_none()
    if not part:
        raise HTTPException(status_code=404, detail="零件不存在")

    if part.lifecycle_state != "已发布":
        raise HTTPException(status_code=400, detail="零件未发布，无法取消发布")

    # 取消发布必须关联已批准的更改通告，确保变更可追溯
    if not change_notice_id:
        raise HTTPException(status_code=400, detail="取消发布需要提供更改通告编号")

    cn_result = await db.execute(select(ChangeNotice).where(ChangeNotice.id == change_notice_id))
    cn = cn_result.scalar_one_or_none()
    if not cn or cn.part_id != part_id:
        raise HTTPException(status_code=400, detail="更改通告不存在或不属于该零件")
    if cn.status != "已批准":
        raise HTTPException(status_code=400, detail="更改通告未经批准，无法取消发布")

    # 更改通告标记为已完成，并递增大版本号（如 A.2 -> B.1）
    cn.status = "已完成"
    new_version = next_major_version(part.current_version or "A.1")
    part.lifecycle_state = "工作中"
    part.check_state = "检入"
    part.current_version = new_version
    await db.commit()
    await db.refresh(part)
    return PartResponse.model_validate(part)


async def find_part_by_number(part_number: str, db: AsyncSession) -> PartResponse | None:
    """根据零件号精确查找零件"""
    result = await db.execute(select(Part).where(Part.part_number == part_number))
    part = result.scalar_one_or_none()
    if part:
        return PartResponse.model_validate(part)
    return None


async def get_latest_version_file(part_id, db: AsyncSession):
    """获取零件最新版本的文件路径和文件名，用于文件下载"""
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

    # 拼接下载文件名：零件号_版本号.扩展名
    part_result = await db.execute(select(Part).where(Part.id == part_id))
    part = part_result.scalar_one_or_none()
    ext = f".{version.file_type}" if version.file_type else ""
    filename = f"{part.part_number}_{version.version_number}{ext}" if part else f"file{ext}"

    return version.file_path, filename


async def delete_part(part_id, db: AsyncSession, user_id):
    """删除零件，级联清理关联的版本记录和 BOM 引用"""
    result = await db.execute(select(Part).where(Part.id == part_id))
    part = result.scalar_one_or_none()
    if not part:
        raise HTTPException(status_code=404, detail="零件不存在")

    if part.check_state == "检出":
        raise HTTPException(status_code=400, detail="零件已检出，无法删除")

    # 删除关联版本记录
    from app.models.version import Version
    versions_result = await db.execute(select(Version).where(Version.part_id == part_id))
    for v in versions_result.scalars().all():
        await db.delete(v)

    # 删除 BOM 引用（该零件作为子件被其他装配体引用的记录）
    from app.models.bom import BomItem
    bom_result = await db.execute(select(BomItem).where(BomItem.part_id == part_id))
    for b in bom_result.scalars().all():
        await db.delete(b)

    # 删除 BOM 子件列表（该零件作为装配体拥有的子件记录）
    bom_assembly_result = await db.execute(select(BomItem).where(BomItem.assembly_id == part_id))
    for b in bom_assembly_result.scalars().all():
        await db.delete(b)

    await db.delete(part)
    await db.commit()
    return {"message": "删除成功"}


async def branch_part(
    source_id, branch_name: str, db: AsyncSession, user_id
) -> PartResponse:
    """从现有零件创建分支（变体），新零件继承源零件的类型和子系统"""
    result = await db.execute(select(Part).where(Part.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="源零件不存在")

    from app.services.version_service import get_next_part_number
    # 有模板则用模板生成新零件号，否则用源零件号加分支名后缀
    if source.template_id:
        next_info = await get_next_part_number(
            source.template_id, source.subsystem or "", db, source.type
        )
        part_number = next_info["part_number"]
    else:
        part_number = f"{source.part_number}-{branch_name}"

    branch = Part(
        part_number=part_number,
        name=f"{source.name} ({branch_name})",
        type=source.type,
        subsystem=source.subsystem,
        template_id=source.template_id,
        current_version="A.1",
        lifecycle_state="工作中",
        check_state="检入",
        derived_from_id=source_id,  # 记录衍生关系
        branch_name=branch_name,
        branch_created_at=datetime.utcnow(),
        created_by=user_id,
    )
    db.add(branch)
    await db.commit()
    await db.refresh(branch)
    return PartResponse.model_validate(branch)


async def get_lineage(part_id, db: AsyncSession) -> list[dict]:
    """获取零件的衍生链（从根节点到当前节点的完整路径）"""
    lineage = []
    current_id = part_id
    visited = set()  # 防止循环引用导致无限遍历

    while current_id and current_id not in visited:
        visited.add(current_id)
        result = await db.execute(select(Part).where(Part.id == current_id))
        part = result.scalar_one_or_none()
        if not part:
            break
        lineage.append({
            "id": str(part.id),
            "part_number": part.part_number,
            "name": part.name,
            "branch_name": part.branch_name,
            "derived_from_id": str(part.derived_from_id) if part.derived_from_id else None,
        })
        current_id = part.derived_from_id

    # 反转为从根到当前的顺序
    lineage.reverse()
    return lineage


async def get_branches(part_id, db: AsyncSession) -> list[PartResponse]:
    """获取零件的所有直接分支（派生自该零件的子零件）"""
    result = await db.execute(
        select(Part).where(Part.derived_from_id == part_id)
    )
    return [PartResponse.model_validate(p) for p in result.scalars().all()]
