from datetime import datetime
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ResearchPlan(BaseModel):
    steps: List[str] = Field(description="Sequential research steps to gather intelligence")
    required_tools: List[str] = Field(description="Allowed tool names for these steps")
    reasoning_summary: str = Field(description="Concise rationale for the plan")


class EvidenceClaim(BaseModel):
    claim: str
    source: str
    confidence: float = 1.0


class PersonalizedEmail(BaseModel):
    subject: str
    opening_line: str
    pain_point: str
    value_proposition: str
    call_to_action: str
    full_body: str
    evidence_claims: List[EvidenceClaim] = []


class ToolCallResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_run_id: uuid.UUID
    tool_name: str
    arguments: Dict[str, Any] = {}
    result: Dict[str, Any] = {}
    status: str
    latency_ms: int
    error: Optional[str] = None
    created_at: datetime


class AgentRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    campaign_id: Optional[uuid.UUID] = None
    lead_id: Optional[uuid.UUID] = None
    agent_type: str
    status: str
    input_json: Dict[str, Any] = {}
    output_json: Dict[str, Any] = {}
    model: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    tool_calls: Optional[List[ToolCallResponse]] = None


class ApprovalActionRequest(BaseModel):
    action: str = Field(description="'APPROVE' or 'REJECT'")
    feedback: Optional[str] = None
    edited_subject: Optional[str] = None
    edited_body: Optional[str] = None


class StreamEvent(BaseModel):
    event: str
    agent_run_id: str
    step: Optional[str] = None
    data: Dict[str, Any] = {}
    timestamp: str
