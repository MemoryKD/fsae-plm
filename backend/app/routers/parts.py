"""
零件路由 - 零件 CRUD、检入检出、发布、分支、下载等 API 端点

端点列表：
- GET    /                     - 列出零件（支持搜索）
- POST   /                     - 手动创建零件
- GET    /next-number          - 预览下一个可用零件号
- POST   /auto-create          - 带文件自动创建零件
- POST   /create-with-template - 模板自动编号创建（无文件）
- GET    /check-number         - 检查零件号是否已存在
- DELETE /{part_id}            - 删除零件
- POST   /{part_id}/branch     - 创建分支
- GET    /{part_id}/lineage    - 查看衍生链
- GET    /{part_id}/branches   - 查看所有分支
- GET    /{part_id}             - 获取零件详情
- POST   /{part_id}/checkout   - 检出零件
- POST   /{part_id}/checkin    - 检入零件
- POST   /{part_id}/publish    - 发布零件
- POST   /{part_id}/unpublish  - 取消发布
- GET    /{part_id}/download   - 下载最新版本文件
- GET    /{part_id}/download-all - 下载装配体及子件 zip 包
- GET    /{part_id}/preview    - 获取 3D 预览文件
- POST   /{part_id}/thumbnail  - 上传缩略图
- GET    /{part_id}/thumbnail  - 获取缩略图
"""
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
    get_latest_version_file, create_part_with_template, delete_part,
    branch_part, get_lineage, get_branches,
)
from app.services.version_service import get_next_part_number
from app.services.auth_service import get_current_user, require_permission
from app.utils.file_storage import get_storage

router = APIRouter()


@router.get("/", response_model=list[PartResponse])
async def get_parts(
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出零件，支持按零件号/名称/子系统模糊搜索"""
    return await list_parts(db, search)


@router.post("/", response_model=PartResponse)
async def create_new_part(
    data: PartCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """手动创建零件（零件号由前端指定）"""
    return await create_part(data, db, current_user.id)


@router.get("/next-number", response_model=NextPartNumberResponse)
async def get_next_number(
    template_id: UUID = Query(...),
    subsystem_code: str = Query(""),
    part_type: str = Query("part"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """预览指定模板+子系统的下一个可用零件号（不实际创建）"""
    return await get_next_part_number(template_id, subsystem_code, db, part_type)


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
    """自动创建零件：自动生成零件号 + 上传文件"""
    return await auto_create_part(name, type, subsystem, template_id, file, db, current_user.id)


@router.post("/create-with-template", response_model=PartResponse)
async def create_with_template(
    data: AutoPartCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """使用模板自动编号创建零件（不需要上传文件）"""
    return await create_part_with_template(
        data.name, data.type, data.subsystem or "", data.template_id, db, current_user.id
    )


@router.get("/check-number")
async def check_part_number(
    number: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """检查零件号是否已存在（用于前端实时校验）"""
    part = await find_part_by_number(number, db)
    return {"exists": part is not None, "part": part}


@router.delete("/{part_id}")
async def delete_part_endpoint(
    part_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("delete_parts")),
):
    """删除零件（需要 delete_parts 权限）"""
    return await delete_part(part_id, db, current_user.id)


@router.post("/{part_id}/branch", response_model=PartResponse)
async def create_branch(
    part_id: UUID,
    branch_name: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """从现有零件创建分支变体"""
    return await branch_part(part_id, branch_name, db, current_user.id)


@router.get("/{part_id}/lineage")
async def get_part_lineage(
    part_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取零件的衍生链（从根到当前节点）"""
    return await get_lineage(part_id, db)


@router.get("/{part_id}/branches", response_model=list[PartResponse])
async def get_part_branches(
    part_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取零件的所有直接分支"""
    return await get_branches(part_id, db)


@router.get("/{part_id}/download-all")
async def download_assembly_all(
    part_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """下载装配体及所有关联零件的最新版本文件（zip 压缩包）"""
    import zipfile
    import tempfile
    from app.services.bom_service import get_assembly_parts
    from app.services.part_service import get_latest_version_file

    # 获取装配体本体文件
    assembly_path, assembly_name = await get_latest_version_file(part_id, db)

    # 获取 BOM 中所有子件
    bom_parts = await get_assembly_parts(part_id, db)

    # 打包为 zip
    tmp = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
    with zipfile.ZipFile(tmp.name, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(assembly_path, assembly_name)
        for bp in bom_parts:
            try:
                fpath, fname = await get_latest_version_file(bp.id, db)
                zf.write(fpath, fname)
            except Exception:
                pass  # 跳过没有文件的零件

    return FileResponse(
        tmp.name,
        media_type="application/zip",
        filename=f"{assembly_name}.zip",
    )


@router.get("/{part_id}/preview")
async def get_3d_preview(
    part_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """返回零件的 3D 预览文件（glTF 二进制格式 .glb）"""
    from app.services.preview_service import get_preview_path
    path = get_preview_path(str(part_id))
    if not path:
        raise HTTPException(status_code=404, detail="3D 预览不可用")
    return FileResponse(path, media_type="model/gltf-binary")


@router.get("/{part_id}", response_model=PartResponse)
async def get_part_detail(
    part_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单个零件详情"""
    return await get_part(part_id, db)


@router.post("/{part_id}/checkout", response_model=PartResponse)
async def checkout(
    part_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("checkout_parts")),
):
    """检出零件（需要 checkout_parts 权限，装配体会级联检出子件）"""
    return await checkout_part(part_id, db, current_user.id)


@router.post("/{part_id}/checkin", response_model=PartResponse)
async def checkin(
    part_id: UUID,
    file: UploadFile = File(...),
    comment: str = Form(""),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("checkin_parts")),
):
    """检入零件（需要 checkin_parts 权限，上传文件并递增小版本）"""
    return await checkin_part(part_id, comment, file, db, current_user.id)


@router.post("/{part_id}/publish", response_model=PartResponse)
async def publish(
    part_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("publish_parts")),
):
    """发布零件（需要 publish_parts 权限，发布后变为只读）"""
    return await publish_part(part_id, db, current_user.id)


@router.post("/{part_id}/unpublish", response_model=PartResponse)
async def unpublish(
    part_id: UUID,
    change_notice_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("unpublish_parts")),
):
    """取消发布零件（需提供已批准的更改通告编号，大版本号递增）"""
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
    """上传零件缩略图（限制 500KB 以内）"""
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
    """获取零件缩略图文件"""
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
