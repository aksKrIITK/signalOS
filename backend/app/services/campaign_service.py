import uuid
from typing import Any, Dict, List, Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.campaign import Campaign, CampaignStatus
from app.db.repositories.campaign_repo import CampaignRepository
from app.schemas.campaign import CampaignCreate, CampaignUpdate
from app.core.exceptions import NotFoundError


class CampaignService:
    """Service layer managing business logic and repository interactions for GTM campaigns."""

    def __init__(self, db: AsyncSession):
        """Initializes the CampaignService with an active database session and repository."""
        self.db = db
        self.campaign_repo = CampaignRepository(db)

    async def create_campaign(
        self,
        organization_id: uuid.UUID,
        campaign_in: CampaignCreate,
    ) -> Campaign:
        """
        Creates a new campaign in DRAFT status with ICP and signal definitions.
        Returns the newly persisted Campaign model.
        """
        return await self.campaign_repo.create(
            organization_id=organization_id,
            name=campaign_in.name,
            description=campaign_in.description,
            status=CampaignStatus.DRAFT,
            icp_definition=campaign_in.icp_definition.model_dump(),
            signal_definition=campaign_in.signal_definition.model_dump(),
        )

    async def get_campaign(self, id: uuid.UUID, organization_id: uuid.UUID) -> Campaign:
        """
        Retrieves a campaign by ID scoped to the organization, raising NotFoundError if absent.
        """
        camp = await self.campaign_repo.get_with_details(id, organization_id)
        if not camp:
            raise NotFoundError(f"Campaign {id} not found")
        return camp

    async def list_campaigns(
        self,
        organization_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[Campaign]:
        """
        Retrieves a paginated list of campaigns belonging to the specified organization.
        """
        return await self.campaign_repo.list(organization_id=organization_id, skip=skip, limit=limit)

    async def update_campaign(
        self,
        id: uuid.UUID,
        organization_id: uuid.UUID,
        update_in: CampaignUpdate,
    ) -> Campaign:
        """
        Updates campaign attributes (name, description, status, ICP, or signal definitions)
        after verifying organization ownership.
        """
        camp = await self.get_campaign(id, organization_id)
        updates = {}
        if update_in.name is not None:
            updates["name"] = update_in.name
        if update_in.description is not None:
            updates["description"] = update_in.description
        if update_in.status is not None:
            updates["status"] = update_in.status
        if update_in.icp_definition is not None:
            updates["icp_definition"] = update_in.icp_definition.model_dump()
        if update_in.signal_definition is not None:
            updates["signal_definition"] = update_in.signal_definition.model_dump()

        return await self.campaign_repo.update(camp, **updates)

    async def get_progress(self, id: uuid.UUID, organization_id: uuid.UUID) -> Dict[str, Any]:
        """
        Calculates execution metrics and lead lifecycle progression for a given campaign.
        """
        return await self.campaign_repo.get_progress(id, organization_id)
