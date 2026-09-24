import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from sqlalchemy import String, Float, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base
from app.db.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.organization import Organization
    from app.db.models.lead import Lead
    from app.db.models.agent_run import AgentRun


class CampaignStatus(str, Enum):
    DRAFT = "DRAFT"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Campaign(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "campaigns"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default=CampaignStatus.DRAFT, nullable=False, index=True)
    icp_definition: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    signal_definition: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="campaigns")
    campaign_leads: Mapped[List["CampaignLead"]] = relationship("CampaignLead", back_populates="campaign", cascade="all, delete-orphan")
    agent_runs: Mapped[List["AgentRun"]] = relationship("AgentRun", back_populates="campaign", cascade="all, delete-orphan")


class CampaignLead(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "campaign_leads"

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(50), default="NEW", nullable=False)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    agent_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="SET NULL"),
        nullable=True,
    )

    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="campaign_leads")
    lead: Mapped["Lead"] = relationship("Lead", back_populates="campaign_associations")
    agent_run: Mapped[Optional["AgentRun"]] = relationship("AgentRun")

    __table_args__ = (
        UniqueConstraint("campaign_id", "lead_id", name="uq_campaign_leads_campaign_lead"),
        Index("ix_campaign_leads_campaign_status", "campaign_id", "status"),
    )
