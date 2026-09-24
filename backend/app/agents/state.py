from typing import Any, Dict, List, Optional, TypedDict


class SDRState(TypedDict, total=False):
    organization_id: str
    campaign_id: str
    lead_id: str
    agent_run_id: str

    objective: str

    company: Dict[str, Any]
    contact: Dict[str, Any]
    icp: Dict[str, Any]

    research_plan: Dict[str, Any]
    research: List[Dict[str, Any]]
    signals: List[Dict[str, Any]]
    retrieved_context: List[Dict[str, Any]]

    score: float
    score_reasons: List[str]
    score_confidence: float

    email_subject: str
    email_body: str
    evidence_claims: List[Dict[str, Any]]

    critic_feedback: str
    critic_passed: bool
    research_iterations: int

    tool_calls: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]

    step_count: int
    total_tokens: int
    total_cost_usd: float

    requires_human_approval: bool
    approved: bool
    action_executed: bool
    action_result: Dict[str, Any]
