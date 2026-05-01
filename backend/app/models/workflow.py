import uuid
from sqlalchemy import Column, String, ForeignKey
from app.utils.types import PortableUUID as UUID, PortableJSON as JSONB

from app.database import Base


class WorkflowTemplate(Base):
    __tablename__ = "workflow_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    states = Column(JSONB, nullable=False)
    transitions = Column(JSONB, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    part_id = Column(UUID(as_uuid=True), ForeignKey("parts.id"), nullable=False, index=True)
    from_state = Column(String(50))
    to_state = Column(String(50))
    approver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    comment = Column(String(500))
