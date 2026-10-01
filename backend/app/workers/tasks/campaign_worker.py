import asyncio
import uuid
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import AsyncSessionLocal
from app.db.models.campaign import CampaignStatus
from app.db.repositories.campaign_repo import CampaignRepository
from app.workers.messaging import message_bus
from app.workers.tasks.agent_worker import execute_agent_pipeline
from app.core.logging import logger


async def process_campaign_batch(
    campaign_id: uuid.UUID,
    organization_id: uuid.UUID,
    batch_size: int = 50,
) -> None:
    """
    High-Throughput Campaign Producer Worker:
    - Queries unprocessed campaign targets.
    - Produces job messages to high-speed message queue (Kafka / Redis Stream).
    - Loose coupling: decouple task production from agent pipeline consumption.
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

    if unprocessed:
        # Publish messages onto message queue for scalable multi-worker processing
        for item in unprocessed:
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
            job_payload = {
                "organization_id": str(organization_id),
                "campaign_id": str(campaign_id),
                "lead_id": str(item.lead_id),
                "icp": campaign.icp_definition,
                "lead_data": lead_data,
            }
            await message_bus.publish(
                topic="agent.runs",
                payload=job_payload,
                key=str(item.lead_id),
            )
        logger.info("campaign_leads_enqueued_to_bus", campaign_id=str(campaign_id), count=len(unprocessed))
    else:
        # If no initial leads, produce discovery task
        job_payload = {
            "organization_id": str(organization_id),
            "campaign_id": str(campaign_id),
            "lead_id": None,
            "icp": campaign.icp_definition,
            "lead_data": {},
        }
        await message_bus.publish(
            topic="agent.runs",
            payload=job_payload,
            key=str(campaign_id),
        )

    async with AsyncSessionLocal() as db:
        campaign_repo = CampaignRepository(db)
        campaign = await campaign_repo.get_by_id(campaign_id, organization_id)
        if campaign:
            await campaign_repo.update(campaign, status=CampaignStatus.COMPLETED)
            await db.commit()

    logger.info("completed_campaign_batch_enqueueing", campaign_id=str(campaign_id))


async def handle_agent_run_consumer_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Consumer Handler for "agent.runs" queue.
    Executed by worker pool through resilient MessageBus retry wrapper.
    """
    org_id = uuid.UUID(payload["organization_id"])
    campaign_id = uuid.UUID(payload["campaign_id"]) if payload.get("campaign_id") else None
    lead_id = uuid.UUID(payload["lead_id"]) if payload.get("lead_id") else None
    icp = payload.get("icp")
    lead_data = payload.get("lead_data")

    res = await execute_agent_pipeline(
        organization_id=org_id,
        campaign_id=campaign_id,
        lead_id=lead_id,
        icp=icp,
        lead_data=lead_data,
    )

    if campaign_id and lead_id:
        async with AsyncSessionLocal() as db_inner:
            cr = CampaignRepository(db_inner)
            cl = await cr.get_campaign_lead(campaign_id, lead_id)
            if cl:
                await cr.update(cl, status="COMPLETED", score=res.get("score"))
            await db_inner.commit()

    return res
