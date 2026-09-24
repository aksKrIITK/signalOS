import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from sqlalchemy import String, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base
from app.db.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.company import Company
    from app.db.models.contact import Contact
    from app.db.models.campaign import CampaignLead


class LeadStatus(str, Enum):
    NEW = "NEW"
    RESEARCHING = "RESEARCHING"
    QUALIFIED = "QUALIFIED"
    DISQUALIFIED = "DISQUALIFIED"
    CONTACTED = "CONTACTED"
    REPLIED = "REPLIED"
    CONVERTED = "CONVERTED"


class Lead(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "leads"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    contact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(50), default=LeadStatus.NEW, nullable=False, index=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    score_reason: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(100), default="agent_discovery", nullable=True)

    company: Mapped["Company"] = relationship("Company", back_populates="leads")
    contact: Mapped[Optional["Contact"]] = relationship("Contact", back_populates="leads")
    campaign_associations: Mapped[List["CampaignLead"]] = relationship("CampaignLead", back_populates="lead", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_leads_org_status", "organization_id", "status"),
        Index("ix_leads_org_score", "organization_id", "score"),
    )
