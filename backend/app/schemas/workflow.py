from uuid import UUID
from pydantic import BaseModel


class WorkflowTransition(BaseModel):
    to_state: str
    comment: str | None = None


class ApprovalResponse(BaseModel):
    id: UUID
    part_id: UUID
    from_state: str | None
    to_state: str | None
    approver_id: UUID | None
    comment: str | None

    class Config:
        from_attributes = True
