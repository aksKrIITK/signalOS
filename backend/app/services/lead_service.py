import uuid
from typing import Any, Dict, Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.lead import Lead, LeadStatus
from app.db.repositories.lead_repo import LeadRepository
from app.schemas.lead import LeadCreate, LeadUpdate
from app.core.exceptions import NotFoundError


class LeadService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.lead_repo = LeadRepository(db)

    async def create_or_update_lead(
        self,
        organization_id: uuid.UUID,
        company_id: uuid.UUID,
        contact_id: Optional[uuid.UUID] = None,
        status: str = LeadStatus.NEW,
        score: Optional[float] = None,
        score_reason: Optional[Dict[str, Any]] = None,
        source: str = "agent_discovery",
    ) -> Lead:
        existing = await self.lead_repo.get_by_company_and_contact(organization_id, company_id, contact_id)
        if existing:
            return await self.lead_repo.update(
                existing,
                status=status if status != LeadStatus.NEW else existing.status,
                score=score if score is not None else existing.score,
                score_reason=score_reason if score_reason else existing.score_reason,
            )

        return await self.lead_repo.create(
            organization_id=organization_id,
            company_id=company_id,
            contact_id=contact_id,
            status=status,
            score=score,
            score_reason=score_reason or {},
            source=source,
        )

    async def get_lead(self, id: uuid.UUID, organization_id: uuid.UUID) -> Lead:
        lead = await self.lead_repo.get_with_details(id, organization_id)
        if not lead:
            raise NotFoundError(f"Lead {id} not found")
        return lead

    async def list_leads(
        self,
        organization_id: uuid.UUID,
        status: Optional[str] = None,
        min_score: Optional[float] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[Lead]:
        return await self.lead_repo.list_leads(
            organization_id=organization_id,
            status=status,
            min_score=min_score,
            skip=skip,
            limit=limit,
        )

    async def update_lead_status(
        self,
        id: uuid.UUID,
        organization_id: uuid.UUID,
        status: str,
        score: Optional[float] = None,
    ) -> Lead:
        lead = await self.get_lead(id, organization_id)
        return await self.lead_repo.update(lead, status=status, score=score)
