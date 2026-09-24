import uuid
from typing import Any, Dict, Optional
from sqlalchemy import String, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base
from app.db.models.base import UUIDMixin, TimestampMixin


class ActionExecution(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "action_executions"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    target_resource_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    result: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    error: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)

    __table_args__ = (
        Index("ix_action_executions_org_status", "organization_id", "status"),
    )
