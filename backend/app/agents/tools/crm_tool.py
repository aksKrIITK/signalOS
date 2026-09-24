from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class CRMCompany(BaseModel):
    id: str
    name: str
    domain: str
    industry: Optional[str] = None
    employee_count: Optional[int] = None
    crm_stage: Optional[str] = None


class CRMContact(BaseModel):
    id: str
    first_name: str
    last_name: Optional[str] = None
    email: Optional[str] = None
    title: Optional[str] = None
    company_id: str


class CRMClient(ABC):
    @abstractmethod
    async def search_companies(self, domain: str) -> List[CRMCompany]:
        pass

    @abstractmethod
    async def search_contacts(self, email: str) -> List[CRMContact]:
        pass

    @abstractmethod
    async def create_activity(self, company_id: str, activity_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        pass


class MockCRMAdapter(CRMClient):
    """Local CRM adapter storing in-memory or mocking Salesforce/HubSpot interactions."""

    async def search_companies(self, domain: str) -> List[CRMCompany]:
        return [
            CRMCompany(
                id="crm-comp-101",
                name="Finflow Systems",
                domain=domain,
                industry="B2B SaaS",
                employee_count=180,
                crm_stage="Uncontacted",
            )
        ]

    async def search_contacts(self, email: str) -> List[CRMContact]:
        return [
            CRMContact(
                id="crm-cont-202",
                first_name="Vikram",
                last_name="Sharma",
                email=email,
                title="VP Engineering",
                company_id="crm-comp-101",
            )
        ]

    async def create_activity(self, company_id: str, activity_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "CREATED",
            "activity_id": f"act-{activity_type}-999",
            "company_id": company_id,
            "details": details,
        }
