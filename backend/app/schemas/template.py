from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    prefix: str = Field(default="", max_length=20)
    separator: str = Field(default="-", max_length=5)
    digit_count: int = Field(default=3, ge=1, le=6)
    subsystem_codes: dict[str, str] = Field(default_factory=dict)


class TemplateUpdate(BaseModel):
    name: str | None = None
    prefix: str | None = None
    separator: str | None = None
    digit_count: int | None = None
    subsystem_codes: dict[str, str] | None = None


class TemplateResponse(BaseModel):
    id: UUID
    name: str
    prefix: str | None
    separator: str
    digit_count: int
    subsystem_codes: dict[str, str]
    created_by: UUID | None
    created_at: datetime

    class Config:
        from_attributes = True
