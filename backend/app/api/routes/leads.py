import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.models.user import User
from app.api.dependencies import get_current_user
from app.services.lead_service import LeadService
from app.schemas.lead import LeadResponse, LeadUpdate

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.get("", response_model=List[LeadResponse])
async def list_leads(
    status: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None, ge=0, le=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = LeadService(db)
    return await service.list_leads(
        organization_id=current_user.organization_id,
        status=status,
        min_score=min_score,
        skip=skip,
        limit=limit,
    )


@router.get("/{id}", response_model=LeadResponse)
async def get_lead(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = LeadService(db)
    return await service.get_lead(id, current_user.organization_id)


@router.patch("/{id}", response_model=LeadResponse)
async def update_lead(
    id: uuid.UUID,
    data: LeadUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = LeadService(db)
    updated = await service.update_lead_status(
        id, current_user.organization_id, status=data.status or "RESEARCHING", score=data.score
    )
    await db.commit()
    return updated
