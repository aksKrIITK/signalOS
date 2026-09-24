import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class ContactCreate(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    email: Optional[str] = None
    job_title: Optional[str] = None
    linkedin_url: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class ContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    company_id: uuid.UUID
    first_name: str
    last_name: Optional[str] = None
    email: Optional[str] = None
    job_title: Optional[str] = None
    linkedin_url: Optional[str] = None
    metadata_json: Dict[str, Any] = {}


class CompanyCreate(BaseModel):
    name: str
    domain: str
    industry: Optional[str] = None
    employee_count: Optional[int] = None
    country: Optional[str] = None
    description: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    domain: str
    industry: Optional[str] = None
    employee_count: Optional[int] = None
    country: Optional[str] = None
    description: Optional[str] = None
    metadata_json: Dict[str, Any] = {}
    contacts: Optional[List[ContactResponse]] = None
