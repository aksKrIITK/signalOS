import uuid
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base
from app.db.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.company import Company
    from app.db.models.lead import Lead


class Contact(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "contacts"

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
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    job_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, nullable=False)

    company: Mapped["Company"] = relationship("Company", back_populates="contacts")
    leads: Mapped[List["Lead"]] = relationship("Lead", back_populates="contact", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_contacts_org_email", "organization_id", "email"),
        Index("ix_contacts_org_company", "organization_id", "company_id"),
    )
