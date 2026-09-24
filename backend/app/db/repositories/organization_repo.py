import uuid
from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.organization import Organization
from app.db.models.user import User
from app.db.repositories.base import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    def __init__(self, db: AsyncSession):
        super().__init__(Organization, db)


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list_by_org(self, organization_id: uuid.UUID) -> Sequence[User]:
        query = select(User).where(User.organization_id == organization_id).order_by(User.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all()
