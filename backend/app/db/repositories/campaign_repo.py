import uuid
from typing import Dict, List, Optional, Sequence
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.campaign import Campaign, CampaignLead
from app.db.repositories.base import BaseRepository


class CampaignRepository(BaseRepository[Campaign]):
    def __init__(self, db: AsyncSession):
        super().__init__(Campaign, db)

    async def get_with_details(self, id: uuid.UUID, organization_id: uuid.UUID) -> Optional[Campaign]:
        query = select(Campaign).where(
            Campaign.id == id,
            Campaign.organization_id == organization_id,
        ).options(
            selectinload(Campaign.campaign_leads).selectinload(CampaignLead.lead),
            selectinload(Campaign.agent_runs),
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_progress(self, campaign_id: uuid.UUID, organization_id: uuid.UUID) -> Dict[str, int]:
        query = select(
            CampaignLead.status,
            func.count(CampaignLead.id)
        ).join(Campaign).where(
            CampaignLead.campaign_id == campaign_id,
            Campaign.organization_id == organization_id,
        ).group_by(CampaignLead.status)
        
        result = await self.db.execute(query)
        status_counts = dict(result.all())
        
        total = sum(status_counts.values())
        processed = sum(v for k, v in status_counts.items() if k in ["COMPLETED", "PROCESSED", "QUALIFIED", "DISQUALIFIED"])
        failed = status_counts.get("FAILED", 0)
        remaining = total - processed - failed
        
        return {
            "total": total,
            "processed": processed,
            "failed": failed,
            "remaining": max(0, remaining),
            "status_breakdown": status_counts,
        }

    async def add_lead_to_campaign(
        self,
        campaign_id: uuid.UUID,
        lead_id: uuid.UUID,
        status: str = "NEW",
    ) -> CampaignLead:
        existing = await self.get_campaign_lead(campaign_id, lead_id)
        if existing:
            return existing
        cl = CampaignLead(campaign_id=campaign_id, lead_id=lead_id, status=status)
        self.db.add(cl)
        await self.db.flush()
        await self.db.refresh(cl)
        return cl

    async def get_campaign_lead(
        self,
        campaign_id: uuid.UUID,
        lead_id: uuid.UUID,
    ) -> Optional[CampaignLead]:
        query = select(CampaignLead).where(
            and_(
                CampaignLead.campaign_id == campaign_id,
                CampaignLead.lead_id == lead_id,
            )
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_unprocessed_batch(
        self,
        campaign_id: uuid.UUID,
        batch_size: int = 50,
        last_id: Optional[uuid.UUID] = None,
    ) -> Sequence[CampaignLead]:
        query = select(CampaignLead).where(
            CampaignLead.campaign_id == campaign_id,
            CampaignLead.status.in_(["NEW", "QUEUED"]),
        ).options(
            selectinload(CampaignLead.lead)
        )
        if last_id:
            query = query.where(CampaignLead.id > last_id)
        query = query.order_by(CampaignLead.created_at.asc()).limit(batch_size)
        result = await self.db.execute(query)
        return result.scalars().all()
