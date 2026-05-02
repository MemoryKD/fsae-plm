from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., max_length=100)
    department: str | None = None
    join_year: str | None = None
    phone: str | None = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: UUID
    username: str
    full_name: str | None = None
    department: str | None = None
    join_year: str | None = None
    phone: str | None = None
    role: str | None = None
    role_id: UUID | None = None
    team: str | None = None
    status: str = "approved"
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    permissions: list[str] = []
