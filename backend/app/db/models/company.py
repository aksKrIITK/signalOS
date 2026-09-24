import uuid
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base
from app.db.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.organization import Organization
    from app.db.models.contact import Contact
    from app.db.models.lead import Lead


class Company(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "companies"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    employee_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, nullable=False)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="companies")
    contacts: Mapped[List["Contact"]] = relationship("Contact", back_populates="company", cascade="all, delete-orphan")
    leads: Mapped[List["Lead"]] = relationship("Lead", back_populates="company", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_companies_org_domain", "organization_id", "domain", unique=True),
        Index("ix_companies_industry", "industry"),
        Index("ix_companies_employee_count", "employee_count"),
        Index("ix_companies_country", "country"),
    )
