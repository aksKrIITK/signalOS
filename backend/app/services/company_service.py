import uuid
from typing import Any, Dict, Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.company import Company
from app.db.models.contact import Contact
from app.db.repositories.company_repo import CompanyRepository, ContactRepository
from app.schemas.company import CompanyCreate, ContactCreate


class CompanyService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.comp_repo = CompanyRepository(db)
        self.cont_repo = ContactRepository(db)

    async def get_or_create_company(
        self,
        organization_id: uuid.UUID,
        company_data: CompanyCreate,
    ) -> Company:
        existing = await self.comp_repo.get_by_domain(organization_id, company_data.domain)
        if existing:
            # Enrich existing company if new data available
            update_fields = {}
            if company_data.employee_count and not existing.employee_count:
                update_fields["employee_count"] = company_data.employee_count
            if company_data.industry and not existing.industry:
                update_fields["industry"] = company_data.industry
            if company_data.country and not existing.country:
                update_fields["country"] = company_data.country
            if update_fields:
                existing = await self.comp_repo.update(existing, **update_fields)
            return existing

        return await self.comp_repo.create(
            organization_id=organization_id,
            name=company_data.name,
            domain=company_data.domain.lower().strip(),
            industry=company_data.industry,
            employee_count=company_data.employee_count,
            country=company_data.country,
            description=company_data.description,
            metadata_json=company_data.metadata_json or {},
        )

    async def get_or_create_contact(
        self,
        organization_id: uuid.UUID,
        company_id: uuid.UUID,
        contact_data: ContactCreate,
    ) -> Contact:
        if contact_data.email:
            existing = await self.cont_repo.get_by_email(organization_id, contact_data.email)
            if existing:
                return existing

        return await self.cont_repo.create(
            organization_id=organization_id,
            company_id=company_id,
            first_name=contact_data.first_name,
            last_name=contact_data.last_name,
            email=contact_data.email.lower().strip() if contact_data.email else None,
            job_title=contact_data.job_title,
            linkedin_url=contact_data.linkedin_url,
            metadata_json=contact_data.metadata_json or {},
        )
