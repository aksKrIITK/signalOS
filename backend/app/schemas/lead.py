import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.company import CompanyResponse, ContactResponse


class LeadScoreBreakdown(BaseModel):
    score: float
    reasons: List[str] = []
    signals: List[str] = []
    confidence: float = 1.0
    deterministic_components: Dict[str, float] = {}
    qualitative_components: Dict[str, float] = {}


class LeadCreate(BaseModel):
    company_id: uuid.UUID
    contact_id: Optional[uuid.UUID] = None
    status: Optional[str] = "NEW"
    score: Optional[float] = None
    score_reason: Optional[Dict[str, Any]] = None
    source: Optional[str] = "manual"


class LeadUpdate(BaseModel):
    status: Optional[str] = None
    score: Optional[float] = None
    score_reason: Optional[Dict[str, Any]] = None


class LeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    company_id: uuid.UUID
    contact_id: Optional[uuid.UUID] = None
    status: str
    score: Optional[float] = None
    score_reason: Dict[str, Any] = {}
    source: Optional[str] = None
    company: Optional[CompanyResponse] = None
    contact: Optional[ContactResponse] = None
