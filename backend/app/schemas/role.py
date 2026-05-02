from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    display_name: str = Field(..., max_length=100)
    permissions: list[str]


class RoleUpdate(BaseModel):
    display_name: str | None = None
    permissions: list[str] | None = None


class RoleResponse(BaseModel):
    id: UUID
    name: str
    display_name: str
    permissions: list[str]
    is_system: str
    created_at: datetime

    class Config:
        from_attributes = True
