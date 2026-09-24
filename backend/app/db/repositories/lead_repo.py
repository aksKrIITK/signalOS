import uuid
from typing import Optional, Sequence
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.lead import Lead
from app.db.models.campaign import CampaignLead
from app.db.repositories.base import BaseRepository


class LeadRepository(BaseRepository[Lead]):
    def __init__(self, db: AsyncSession):
        super().__init__(Lead, db)

    async def get_with_details(self, id: uuid.UUID, organization_id: uuid.UUID) -> Optional[Lead]:
        query = select(Lead).where(
            Lead.id == id,
            Lead.organization_id == organization_id,
        ).options(
            selectinload(Lead.company),
            selectinload(Lead.contact),
            selectinload(Lead.campaign_associations).selectinload(CampaignLead.campaign),
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list_leads(
        self,
        organization_id: uuid.UUID,
        status: Optional[str] = None,
        min_score: Optional[float] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[Lead]:
        query = select(Lead).where(Lead.organization_id == organization_id).options(
            selectinload(Lead.company),
            selectinload(Lead.contact),
        )
        if status:
            query = query.where(Lead.status == status)
        if min_score is not None:
            query = query.where(Lead.score >= min_score)
        query = query.order_by(Lead.score.desc().nullslast(), Lead.created_at.desc())
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_company_and_contact(
        self,
        organization_id: uuid.UUID,
        company_id: uuid.UUID,
        contact_id: Optional[uuid.UUID] = None,
    ) -> Optional[Lead]:
        query = select(Lead).where(
            Lead.organization_id == organization_id,
            Lead.company_id == company_id,
        )
        if contact_id:
            query = query.where(Lead.contact_id == contact_id)
        result = await self.db.execute(query)
        return result.scalars().first()
