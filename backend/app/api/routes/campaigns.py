import asyncio
import uuid
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.models.user import User
from app.api.dependencies import get_current_user
from app.services.campaign_service import CampaignService
from app.schemas.campaign import (
    CampaignCreate,
    CampaignProgressResponse,
    CampaignResponse,
    CampaignRunResponse,
    CampaignUpdate,
)
from app.workers.tasks.campaign_worker import process_campaign_batch

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    data: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CampaignService(db)
    campaign = await service.create_campaign(current_user.organization_id, data)
    await db.commit()
    return campaign


@router.get("", response_model=List[CampaignResponse])
async def list_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CampaignService(db)
    campaigns = await service.list_campaigns(current_user.organization_id, skip=skip, limit=limit)
    return campaigns


@router.get("/{id}", response_model=CampaignResponse)
async def get_campaign(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CampaignService(db)
    return await service.get_campaign(id, current_user.organization_id)


@router.patch("/{id}", response_model=CampaignResponse)
async def update_campaign(
    id: uuid.UUID,
    data: CampaignUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CampaignService(db)
    updated = await service.update_campaign(id, current_user.organization_id, data)
    await db.commit()
    return updated


@router.post("/{id}/run", response_model=CampaignRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_campaign(
    id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CampaignService(db)
    campaign = await service.get_campaign(id, current_user.organization_id)
    job_id = f"job-camp-{uuid.uuid4().hex[:8]}"

    # Dispatch asynchronous campaign batch processing
    background_tasks.add_task(
        process_campaign_batch,
        campaign_id=campaign.id,
        organization_id=current_user.organization_id,
    )

    return CampaignRunResponse(
        job_id=job_id,
        status="QUEUED",
        message="Campaign execution started in background queue",
    )


@router.post("/{id}/pause", response_model=CampaignResponse)
async def pause_campaign(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CampaignService(db)
    updated = await service.update_campaign(
        id, current_user.organization_id, CampaignUpdate(status="PAUSED")
    )
    await db.commit()
    return updated


@router.get("/{id}/progress", response_model=CampaignProgressResponse)
async def get_campaign_progress(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CampaignService(db)
    progress = await service.get_progress(id, current_user.organization_id)
    return CampaignProgressResponse(**progress)
