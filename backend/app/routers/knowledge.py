from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.knowledge import KnowledgeCategory, KnowledgeArticle, KnowledgeAttachment
from app.models.user import User
from app.schemas.knowledge import (
    CategoryCreate, CategoryUpdate, CategoryResponse,
    ArticleCreate, ArticleUpdate, ArticleResponse, ArticleListResponse,
    AttachmentResponse,
)
from app.services.auth_service import get_current_user
from app.utils.file_storage import get_storage

router = APIRouter()


# ========== Categories ==========

@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(KnowledgeCategory).order_by(KnowledgeCategory.sort_order))
    return [CategoryResponse.model_validate(c) for c in result.scalars().all()]


@router.post("/categories", response_model=CategoryResponse)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin", "manager"):
        raise HTTPException(status_code=403, detail="权限不足")
    cat = KnowledgeCategory(**data.model_dump())
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return CategoryResponse.model_validate(cat)


@router.put("/categories/{cat_id}", response_model=CategoryResponse)
async def update_category(
    cat_id: UUID,
    data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin", "manager"):
        raise HTTPException(status_code=403, detail="权限不足")
    result = await db.execute(select(KnowledgeCategory).where(KnowledgeCategory.id == cat_id))
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="板块不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(cat, key, value)
    await db.commit()
    await db.refresh(cat)
    return CategoryResponse.model_validate(cat)


@router.delete("/categories/{cat_id}")
async def delete_category(
    cat_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin", "manager"):
        raise HTTPException(status_code=403, detail="权限不足")
    result = await db.execute(select(KnowledgeCategory).where(KnowledgeCategory.id == cat_id))
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="板块不存在")
    await db.delete(cat)
    await db.commit()
    return {"message": "已删除"}


# ========== Articles ==========

@router.get("/articles", response_model=list[ArticleListResponse])
async def list_articles(
    category_id: UUID | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(KnowledgeArticle)
    if category_id:
        query = query.where(KnowledgeArticle.category_id == category_id)
    if search:
        query = query.where(
            or_(
                KnowledgeArticle.title.ilike(f"%{search}%"),
                KnowledgeArticle.tags.ilike(f"%{search}%"),
            )
        )
    query = query.order_by(KnowledgeArticle.updated_at.desc())
    result = await db.execute(query)
    articles = result.scalars().all()

    enriched = []
    for a in articles:
        resp = ArticleListResponse.model_validate(a)
        if a.author_id:
            u = await db.execute(select(User).where(User.id == a.author_id))
            user = u.scalar_one_or_none()
            if user:
                resp.author_name = user.username
        enriched.append(resp)
    return enriched


@router.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(KnowledgeArticle).where(KnowledgeArticle.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    resp = ArticleResponse.model_validate(article)
    if article.author_id:
        u = await db.execute(select(User).where(User.id == article.author_id))
        user = u.scalar_one_or_none()
        if user:
            resp.author_name = user.username
    return resp


@router.post("/articles", response_model=ArticleResponse)
async def create_article(
    data: ArticleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    article = KnowledgeArticle(**data.model_dump(), author_id=current_user.id)
    db.add(article)
    await db.commit()
    await db.refresh(article)
    resp = ArticleResponse.model_validate(article)
    resp.author_name = current_user.username
    return resp


@router.put("/articles/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: UUID,
    data: ArticleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(KnowledgeArticle).where(KnowledgeArticle.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(article, key, value)
    await db.commit()
    await db.refresh(article)
    return ArticleResponse.model_validate(article)


@router.delete("/articles/{article_id}")
async def delete_article(
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(KnowledgeArticle).where(KnowledgeArticle.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    if article.author_id != current_user.id and current_user.role not in ("admin", "manager"):
        raise HTTPException(status_code=403, detail="只能删除自己的文章")
    await db.delete(article)
    await db.commit()
    return {"message": "已删除"}


# ========== Attachments ==========

@router.get("/articles/{article_id}/attachments", response_model=list[AttachmentResponse])
async def list_attachments(article_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(KnowledgeAttachment).where(KnowledgeAttachment.article_id == article_id)
    )
    return [AttachmentResponse.model_validate(a) for a in result.scalars().all()]


@router.post("/articles/{article_id}/attachments", response_model=AttachmentResponse)
async def upload_attachment(
    article_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(KnowledgeArticle).where(KnowledgeArticle.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    content = await file.read()
    storage = get_storage()
    file_path, file_size = await storage.save(content, f"kb/{file.filename}")

    attachment = KnowledgeAttachment(
        article_id=article_id,
        filename=file.filename or "file",
        file_path=file_path,
        file_size=file_size,
        uploaded_by=current_user.id,
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)
    return AttachmentResponse.model_validate(attachment)


@router.get("/attachments/{attachment_id}/download")
async def download_attachment(attachment_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(KnowledgeAttachment).where(KnowledgeAttachment.id == attachment_id))
    att = result.scalar_one_or_none()
    if not att:
        raise HTTPException(status_code=404, detail="附件不存在")
    return FileResponse(att.file_path, filename=att.filename)


@router.delete("/attachments/{attachment_id}")
async def delete_attachment(
    attachment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(KnowledgeAttachment).where(KnowledgeAttachment.id == attachment_id))
    att = result.scalar_one_or_none()
    if not att:
        raise HTTPException(status_code=404, detail="附件不存在")
    if att.uploaded_by != current_user.id and current_user.role not in ("admin", "manager"):
        raise HTTPException(status_code=403, detail="权限不足")
    await db.delete(att)
    await db.commit()
    return {"message": "已删除"}
