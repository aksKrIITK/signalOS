import asyncio
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import AsyncSessionLocal
from app.db.models.campaign import CampaignStatus
from app.db.repositories.campaign_repo import CampaignRepository
from app.workers.tasks.agent_worker import execute_agent_pipeline
from app.core.logging import logger


async def process_campaign_batch(
    campaign_id: uuid.UUID,
    organization_id: uuid.UUID,
    batch_size: int = 50,
) -> None:
    """
    Campaign Batch Worker:
    - Queries unprocessed leads using cursor pagination.
    - Dispatches agent workflows concurrently with concurrency throttling.
    - Updates campaign progress and handles failure state.
    """
    logger.info("starting_campaign_batch_processing", campaign_id=str(campaign_id))

    async with AsyncSessionLocal() as db:
        campaign_repo = CampaignRepository(db)
        campaign = await campaign_repo.get_by_id(campaign_id, organization_id)
        if not campaign:
            return

        await campaign_repo.update(campaign, status=CampaignStatus.RUNNING)
        await db.commit()

        unprocessed = await campaign_repo.get_unprocessed_batch(campaign_id, batch_size=batch_size)

    # Process items with controlled concurrency (e.g., semaphore of 5)
    semaphore = asyncio.Semaphore(5)

    async def _process_item(item):
        async with semaphore:
            lead_data = {
                "company": {
                    "name": item.lead.company.name if item.lead and item.lead.company else "Discovered Target",
                    "domain": item.lead.company.domain if item.lead and item.lead.company else "target.io",
                    "industry": item.lead.company.industry if item.lead and item.lead.company else "B2B SaaS",
                },
                "contact": {
                    "first_name": item.lead.contact.first_name if item.lead and item.lead.contact else "Tech",
                    "last_name": item.lead.contact.last_name if item.lead and item.lead.contact else "Leader",
                    "job_title": item.lead.contact.job_title if item.lead and item.lead.contact else "CTO",
                } if item.lead and item.lead.contact else {},
            }
            try:
                res = await execute_agent_pipeline(
                    organization_id=organization_id,
                    campaign_id=campaign_id,
                    lead_id=item.lead_id,
                    icp=campaign.icp_definition,
                    lead_data=lead_data,
                )
                async with AsyncSessionLocal() as db_inner:
                    cr = CampaignRepository(db_inner)
                    cl = await cr.get_campaign_lead(campaign_id, item.lead_id)
                    if cl:
                        await cr.update(cl, status="COMPLETED", score=res.get("score"))
                    await db_inner.commit()
            except Exception as e:
                logger.warning("campaign_item_failed", lead_id=str(item.lead_id), error=str(e))
                async with AsyncSessionLocal() as db_inner:
                    cr = CampaignRepository(db_inner)
                    cl = await cr.get_campaign_lead(campaign_id, item.lead_id)
                    if cl:
                        await cr.update(cl, status="FAILED")
                    await db_inner.commit()

    if unprocessed:
        await asyncio.gather(*[_process_item(item) for item in unprocessed])
    else:
        # If no initial leads, execute seed discovery run
        await execute_agent_pipeline(
            organization_id=organization_id,
            campaign_id=campaign_id,
            icp=campaign.icp_definition,
            lead_data={},
        )

    async with AsyncSessionLocal() as db:
        campaign_repo = CampaignRepository(db)
        campaign = await campaign_repo.get_by_id(campaign_id, organization_id)
        if campaign:
            await campaign_repo.update(campaign, status=CampaignStatus.COMPLETED)
            await db.commit()

    logger.info("completed_campaign_batch_processing", campaign_id=str(campaign_id))
