"""
版本模型 - 零件文件版本记录

每次检入（checkin）操作会创建一条新版本记录，版本号格式为 "大版本.小版本"。
文件存储在物理磁盘上，file_path 记录相对路径。
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, BigInteger, DateTime, Text, ForeignKey
from app.utils.types import PortableUUID as UUID

from app.database import Base


class Version(Base):
    """零件的单次版本快照，关联具体文件和变更说明"""

    __tablename__ = "versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # 所属零件 ID
    part_id = Column(UUID(as_uuid=True), ForeignKey("parts.id"), nullable=False, index=True)
    # 版本号，如 "A.1"、"B.3"
    version_number = Column(String(10), nullable=False)
    # 文件在存储系统中的路径
    file_path = Column(String(500))
    file_size = Column(BigInteger)
    # 文件扩展名，如 "CATPart"、"step"
    file_type = Column(String(50))
    # 版本变更说明（检入时填写）
    comment = Column(Text)
    # 文件 SHA-256 哈希值，用于检入校验（防止重复上传、校验文件一致性）
    file_hash = Column(String(64))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
