from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class PartCreate(BaseModel):
    part_number: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    type: str = Field(default="part")
    subsystem: str | None = None
    template_id: UUID | None = None


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
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
