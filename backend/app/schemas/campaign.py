import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ICPDefinition(BaseModel):
    industry: Optional[str] = "B2B SaaS"
    location: Optional[str] = "India"
    min_employees: Optional[int] = 50
    max_employees: Optional[int] = 500
    target_personas: List[str] = Field(default_factory=lambda: ["CTO", "VP Engineering", "Head of Engineering"])
    tech_stack_keywords: List[str] = Field(default_factory=lambda: ["React", "Python", "AWS", "FastAPI"])


class SignalDefinition(BaseModel):
    required_signals: List[str] = Field(
        default_factory=lambda: [
            "recent funding",
            "hiring engineers",
            "new product launch",
            "technology migration",
            "rapid growth",
        ]
    )
    signal_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "recent funding": 0.35,
            "hiring engineers": 0.25,
            "new product launch": 0.20,
            "technology migration": 0.10,
            "rapid growth": 0.10,
        }
    )


class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    icp_definition: ICPDefinition = Field(default_factory=ICPDefinition)
    signal_definition: SignalDefinition = Field(default_factory=SignalDefinition)


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    icp_definition: Optional[ICPDefinition] = None
    signal_definition: Optional[SignalDefinition] = None


class CampaignProgressResponse(BaseModel):
    total: int
    processed: int
    failed: int
    remaining: int
    status_breakdown: Dict[str, int] = {}


class CampaignResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: Optional[str] = None
    status: str
    icp_definition: Dict[str, Any] = {}
    signal_definition: Dict[str, Any] = {}
    progress: Optional[CampaignProgressResponse] = None

    class Config:
        from_attributes = True


class CampaignRunResponse(BaseModel):
    job_id: str
    status: str
    message: str
