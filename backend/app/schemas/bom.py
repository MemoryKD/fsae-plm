from uuid import UUID
from pydantic import BaseModel, Field


class BomItemCreate(BaseModel):
    part_id: UUID
    quantity: int = Field(default=1, ge=1)
    level: int = Field(default=0, ge=0)


class BomItemResponse(BaseModel):
    id: UUID
    assembly_id: UUID
    part_id: UUID
    quantity: int
    level: int

    class Config:
        from_attributes = True
