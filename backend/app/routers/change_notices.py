from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.change_notice import ChangeNotice
from app.schemas.change_notice import (
    ChangeNoticeCreate, ChangeNoticeResponse, ChangeNoticeApprove,
)
from app.services.auth_service import get_current_user

router = APIRouter()


@router.get("/", response_model=list[ChangeNoticeResponse])
async def list_change_notices(
    part_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(ChangeNotice)
    if part_id:
        query = query.where(ChangeNotice.part_id == part_id)
    query = query.order_by(ChangeNotice.created_at.desc())
    result = await db.execute(query)
    return [ChangeNoticeResponse.model_validate(cn) for cn in result.scalars().all()]


@router.post("/", response_model=ChangeNoticeResponse)
async def create_change_notice(
    data: ChangeNoticeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import datetime
    year = datetime.utcnow().year
    count_result = await db.execute(
        select(ChangeNotice).where(
            ChangeNotice.notice_number.like(f"ECN-{year}-%")
        )
    )
    count = len(count_result.scalars().all())
    notice_number = f"ECN-{year}-{count + 1:04d}"

    cn = ChangeNotice(
        notice_number=notice_number,
        title=data.title,
        description=data.description,
        reason=data.reason,
        part_id=data.part_id,
        created_by=current_user.id,
    )
    db.add(cn)
    await db.commit()
    await db.refresh(cn)
    return ChangeNoticeResponse.model_validate(cn)


@router.get("/{notice_id}", response_model=ChangeNoticeResponse)
async def get_change_notice(
    notice_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(ChangeNotice).where(ChangeNotice.id == notice_id))
    cn = result.scalar_one_or_none()
    if not cn:
        raise HTTPException(status_code=404, detail="更改通告不存在")
    return ChangeNoticeResponse.model_validate(cn)


@router.post("/{notice_id}/approve", response_model=ChangeNoticeResponse)
async def approve_change_notice(
    notice_id: UUID,
    data: ChangeNoticeApprove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(ChangeNotice).where(ChangeNotice.id == notice_id))
    cn = result.scalar_one_or_none()
    if not cn:
        raise HTTPException(status_code=404, detail="更改通告不存在")

    if cn.status != "待审批":
        raise HTTPException(status_code=400, detail="该通告不在待审批状态")

    cn.status = "已批准" if data.approved else "已拒绝"
    cn.approved_by = current_user.id
    await db.commit()
    await db.refresh(cn)
    return ChangeNoticeResponse.model_validate(cn)
