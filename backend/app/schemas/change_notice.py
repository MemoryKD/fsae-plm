from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class ChangeNoticeCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: str | None = None
    reason: str = Field(..., min_length=1)
    part_id: UUID


class ChangeNoticeResponse(BaseModel):
    id: UUID
    notice_number: str
    title: str
    description: str | None
    reason: str
    part_id: UUID
    status: str
    created_by: UUID | None
    approved_by: UUID | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChangeNoticeApprove(BaseModel):
    approved: bool
    comment: str | None = None
