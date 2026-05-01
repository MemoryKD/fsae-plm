from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.part import Part
from app.models.workflow import Approval
from app.schemas.workflow import WorkflowTransition, ApprovalResponse
from app.services.workflow_engine import WorkflowEngine
from app.services.auth_service import get_current_user

router = APIRouter()


@router.post("/parts/{part_id}/transition", response_model=ApprovalResponse)
async def transition_state(
    part_id: UUID,
    data: WorkflowTransition,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Part).where(Part.id == part_id))
    part = result.scalar_one_or_none()
    if not part:
        raise HTTPException(status_code=404, detail="零件不存在")

    engine = WorkflowEngine(
        states=["设计中", "审核中", "已发布"],
        transitions=[
            {"from": "设计中", "to": "审核中", "roles": ["designer", "manager", "admin"]},
            {"from": "审核中", "to": "已发布", "roles": ["manager", "admin"]},
            {"from": "审核中", "to": "设计中", "roles": ["manager", "admin"]},
        ]
    )

    if not engine.can_transition(part.workflow_state, data.to_state, current_user.role):
        raise HTTPException(status_code=403, detail="无权执行此状态转换")

    approval = Approval(
        part_id=part_id, from_state=part.workflow_state,
        to_state=data.to_state, approver_id=current_user.id, comment=data.comment,
    )
    db.add(approval)
    part.workflow_state = data.to_state
    await db.commit()
    await db.refresh(approval)
    return ApprovalResponse.model_validate(approval)


@router.get("/parts/{part_id}/history", response_model=list[ApprovalResponse])
async def get_workflow_history(
    part_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Approval).where(Approval.part_id == part_id))
    return [ApprovalResponse.model_validate(a) for a in result.scalars().all()]
