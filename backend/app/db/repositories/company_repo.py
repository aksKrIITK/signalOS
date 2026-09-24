import uuid
from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.company import Company
from app.db.models.contact import Contact
from app.db.repositories.base import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    def __init__(self, db: AsyncSession):
        super().__init__(Company, db)

    async def get_by_domain(self, organization_id: uuid.UUID, domain: str) -> Optional[Company]:
        query = select(Company).where(
            Company.organization_id == organization_id,
            Company.domain == domain.lower().strip(),
        ).options(selectinload(Company.contacts))
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_with_details(self, id: uuid.UUID, organization_id: uuid.UUID) -> Optional[Company]:
        query = select(Company).where(
            Company.id == id,
            Company.organization_id == organization_id,
        ).options(selectinload(Company.contacts), selectinload(Company.leads))
        result = await self.db.execute(query)
        return result.scalars().first()


class ContactRepository(BaseRepository[Contact]):
    def __init__(self, db: AsyncSession):
        super().__init__(Contact, db)

    async def get_by_email(self, organization_id: uuid.UUID, email: str) -> Optional[Contact]:
        query = select(Contact).where(
            Contact.organization_id == organization_id,
            Contact.email == email.lower().strip(),
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list_by_company(self, organization_id: uuid.UUID, company_id: uuid.UUID) -> Sequence[Contact]:
        query = select(Contact).where(
            Contact.organization_id == organization_id,
            Contact.company_id == company_id,
        )
        result = await self.db.execute(query)
        return result.scalars().all()
