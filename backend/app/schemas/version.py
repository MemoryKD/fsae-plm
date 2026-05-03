from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class VersionCreate(BaseModel):
    version_number: str
    comment: str | None = None


class VersionResponse(BaseModel):
    id: UUID
    part_id: UUID
    version_number: str
    file_path: str | None
    file_size: int | None
    file_type: str | None
    file_hash: str | None = None
    comment: str | None
    created_by: UUID | None
    created_at: datetime

    class Config:
        from_attributes = True
