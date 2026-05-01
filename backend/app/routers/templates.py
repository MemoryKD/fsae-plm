from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.template import PartNumberTemplate
from app.models.user import User
from app.schemas.template import TemplateCreate, TemplateUpdate, TemplateResponse
from app.services.auth_service import get_current_user

router = APIRouter()


@router.get("/", response_model=list[TemplateResponse])
async def list_templates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PartNumberTemplate))
    return [TemplateResponse.model_validate(t) for t in result.scalars().all()]


@router.post("/", response_model=TemplateResponse)
async def create_template(
    data: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin", "manager"):
        raise HTTPException(status_code=403, detail="权限不足")
    template = PartNumberTemplate(**data.model_dump(), created_by=current_user.id)
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return TemplateResponse.model_validate(template)


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: UUID,
    data: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin", "manager"):
        raise HTTPException(status_code=403, detail="权限不足")
    result = await db.execute(select(PartNumberTemplate).where(PartNumberTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(template, key, value)
    await db.commit()
    await db.refresh(template)
    return TemplateResponse.model_validate(template)
