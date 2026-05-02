"""
知识库模型 - 团队技术文档管理

包含三个模型：
- KnowledgeCategory：知识分类（如设计规范、赛事规则、技术笔记）
- KnowledgeArticle：知识文章，支持标签和富文本内容
- KnowledgeAttachment：文章附件，级联删除
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from app.utils.types import PortableUUID as UUID

from app.database import Base


class KnowledgeCategory(Base):
    """知识库分类，用于组织和归类技术文档"""

    __tablename__ = "knowledge_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(500))
    # 前端图标组件名，如 "Document"、"Setting"
    icon = Column(String(50), default="Document")
    # 排序权重，数值越小越靠前
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class KnowledgeArticle(Base):
    """知识库文章，支持分类、标签和附件"""

    __tablename__ = "knowledge_articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False, index=True)
    # 文章正文内容（富文本/Markdown）
    content = Column(Text, default="")
    # 所属分类
    category_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_categories.id"), nullable=False, index=True)
    # 标签，逗号分隔，如 "CATIA,底盘设计,碳纤维"
    tags = Column(String(500), default="")
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class KnowledgeAttachment(Base):
    """知识库文章的附件，随文章删除而级联删除"""

    __tablename__ = "knowledge_attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # 所属文章，ondelete="CASCADE" 实现级联删除
    article_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_articles.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
