from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6)
    role: str = Field(default="designer")
    team: str | None = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: UUID
    username: str
    role: str
    team: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
