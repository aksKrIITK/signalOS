import uuid
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.repositories.organization_repo import OrganizationRepository, UserRepository
from app.api.dependencies import get_current_user, require_roles
from app.db.models.user import User
from app.core.security import UserRole

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get("/current")
async def get_current_organization(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    org_repo = OrganizationRepository(db)
    user_repo = UserRepository(db)

    org = await org_repo.get_by_id(current_user.organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    members = await user_repo.list_by_org(current_user.organization_id)
    return {
        "id": org.id,
        "name": org.name,
        "created_at": org.created_at,
        "members": [
            {"id": m.id, "email": m.email, "full_name": m.full_name, "role": m.role}
            for m in members
        ],
    }


@router.get("/{id}")
async def get_organization_by_id(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.organization_id != id and current_user.role != UserRole.OWNER:
        raise HTTPException(status_code=403, detail="Not authorized to access this organization")

    org_repo = OrganizationRepository(db)
    org = await org_repo.get_by_id(id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org
