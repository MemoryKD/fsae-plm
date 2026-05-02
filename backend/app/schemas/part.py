from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class PartCreate(BaseModel):
    part_number: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    type: str = Field(default="part")
    subsystem: str | None = None
    template_id: UUID | None = None
    derived_from_id: UUID | None = None
    branch_name: str | None = None


class PartUpdate(BaseModel):
    name: str | None = None
    subsystem: str | None = None


class PartResponse(BaseModel):
    id: UUID
    part_number: str
    name: str
    type: str
    subsystem: str | None
    current_version: str | None
    workflow_state: str
    lifecycle_state: str
    check_state: str
    checked_out_by: UUID | None
    thumbnail_path: str | None
    derived_from_id: UUID | None = None
    branch_name: str | None = None
    branch_created_at: datetime | None = None
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PartCheckout(BaseModel):
    message: str = "检出成功"


class PartCheckin(BaseModel):
    comment: str | None = None


class PartPublish(BaseModel):
    message: str = "发布成功"


class NextPartNumberResponse(BaseModel):
    part_number: str
    template_name: str
    subsystem_code: str
    type_code: str = ""


class AutoPartCreate(BaseModel):
    name: str = Field(..., max_length=200)
    type: str = Field(default="part")
    subsystem: str | None = None
    template_id: UUID | None = None
