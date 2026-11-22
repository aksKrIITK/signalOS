from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class CRMCompany(BaseModel):
    """
    Schema representing a CRM company/account record.

    Attributes:
        id (str): CRM-assigned unique company identifier.
        name (str): Company name.
        domain (str): Primary corporate domain.
        industry (Optional[str]): Industry classification.
        employee_count (Optional[int]): Total headcount.
        crm_stage (Optional[str]): Current CRM lifecycle stage.
    """
    id: str
    name: str
    domain: str
    industry: Optional[str] = None
    employee_count: Optional[int] = None
    crm_stage: Optional[str] = None


class CRMContact(BaseModel):
    """
    Schema representing a CRM lead or contact record.

    Attributes:
        id (str): CRM-assigned unique contact identifier.
        first_name (str): Given name.
        last_name (Optional[str]): Family name.
        email (Optional[str]): Primary email address.
        title (Optional[str]): Business title or seniority.
        company_id (str): Foreign key to associated CRM company.
    """
    id: str
    first_name: str
    last_name: Optional[str] = None
    email: Optional[str] = None
    title: Optional[str] = None
    company_id: str


class CRMClient(ABC):
    """Abstract interface defining the CRM adapter contract."""

    @abstractmethod
    async def search_companies(self, domain: str) -> List[CRMCompany]:
        """Searches for companies matching the domain."""
        pass

    @abstractmethod
    async def search_contacts(self, email: str) -> List[CRMContact]:
        """Searches for contacts matching the email."""
        pass

    @abstractmethod
    async def create_activity(self, company_id: str, activity_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Logs an activity against a company in the CRM."""
        pass


class MockCRMAdapter(CRMClient):
    """Local CRM adapter storing in-memory or mocking Salesforce/HubSpot interactions."""

    async def search_companies(self, domain: str) -> List[CRMCompany]:
        """
        Simulates looking up company accounts in CRM by domain.

        Args:
            domain (str): Target web domain to search.

        Returns:
            List[CRMCompany]: Matched company entities.
        """
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
        """
        Simulates looking up contacts in CRM by email address.

        Args:
            email (str): Target email address.

        Returns:
            List[CRMContact]: Matched contact entities.
        """
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
        """
        Simulates creating an activity or engagement touchpoint in the CRM.

        Args:
            company_id (str): Target company ID.
            activity_type (str): Type of activity (e.g. 'call', 'email').
            details (Dict[str, Any]): Activity metadata payload.

        Returns:
            Dict[str, Any]: Execution status and mock activity reference.
        """
        return {
            "status": "CREATED",
            "activity_id": f"act-{activity_type}-999",
            "company_id": company_id,
            "details": details,
        }
