from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    icon: str = Field(default="Document", max_length=50)
    sort_order: int = Field(default=0)


class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    icon: str | None = None
    sort_order: int | None = None


class CategoryResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    icon: str
    sort_order: int
    created_at: datetime

    class Config:
        from_attributes = True


class ArticleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(default="")
    category_id: UUID
    tags: str = Field(default="", max_length=500)


class ArticleUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    category_id: UUID | None = None
    tags: str | None = None


class ArticleResponse(BaseModel):
    id: UUID
    title: str
    content: str
    category_id: UUID
    tags: str | None
    author_id: UUID | None
    author_name: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ArticleListResponse(BaseModel):
    id: UUID
    title: str
    category_id: UUID
    tags: str | None
    author_name: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AttachmentResponse(BaseModel):
    id: UUID
    article_id: UUID
    filename: str
    file_size: int | None
    uploaded_by: UUID | None
    created_at: datetime

    class Config:
        from_attributes = True
