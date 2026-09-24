import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base
from app.db.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.campaign import Campaign


class AgentRunStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AgentRun(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_runs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    campaign_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    lead_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    agent_type: Mapped[str] = mapped_column(String(50), default="sdr_pipeline", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=AgentRunStatus.QUEUED, nullable=False, index=True)
    input_json: Mapped[Dict[str, Any]] = mapped_column("input", JSONB, default=dict, nullable=False)
    output_json: Mapped[Dict[str, Any]] = mapped_column("output", JSONB, default=dict, nullable=False)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)

    campaign: Mapped[Optional["Campaign"]] = relationship("Campaign", back_populates="agent_runs")
    tool_calls: Mapped[List["ToolCall"]] = relationship("ToolCall", back_populates="agent_run", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_agent_runs_org_status", "organization_id", "status"),
        Index("ix_agent_runs_campaign_lead", "campaign_id", "lead_id"),
    )


class ToolCall(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tool_calls"

    agent_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    arguments: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    result: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="SUCCESS", nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)

    agent_run: Mapped["AgentRun"] = relationship("AgentRun", back_populates="tool_calls")
