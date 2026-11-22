from typing import Any, Dict, List, Optional, TypedDict


class SDRState(TypedDict, total=False):
    """
    State schema for the autonomous SDR LangGraph pipeline.

    Maintains accumulated context across discovery, research, signal detection,
    RAG retrieval, qualification scoring, personalized copywriting, hallucination
    auditing, and human-in-the-loop approval workflows.

    Attributes:
        organization_id (str): Tenant organization identifier.
        campaign_id (str): Associated GTM campaign ID.
        lead_id (str): Target lead identifier.
        agent_run_id (str): Unique identifier for this agent run.
        objective (str): Execution goal or campaign outreach prompt.
        company (Dict[str, Any]): Discovered or enriched company profile.
        contact (Dict[str, Any]): Target decision-maker contact information.
        icp (Dict[str, Any]): Campaign Ideal Customer Profile definition.
        research_plan (Dict[str, Any]): Structured plan produced by planner node.
        research (List[Dict[str, Any]]): Collected research dossier items and web snippets.
        signals (List[Dict[str, Any]]): Detected buying signals with citations.
        retrieved_context (List[Dict[str, Any]]): Internal knowledge chunks from RAG.
        score (float): Numerical qualification score (0-100).
        score_reasons (List[str]): Rationale breakdown for lead qualification score.
        score_confidence (float): Confidence score for qualification calculation.
        email_subject (str): Generated personalized email subject line.
        email_body (str): Generated personalized email copy.
        evidence_claims (List[Dict[str, Any]]): Specific factual claims mapped to sources.
        critic_feedback (str): Audit remarks from the critic node.
        critic_passed (bool): Whether drafted email passed hallucination checks.
        research_iterations (int): Counter for research loop cycles.
        tool_calls (List[Dict[str, Any]]): Audit log of sequential tool executions.
        errors (List[Dict[str, Any]]): Trapped non-fatal runtime errors.
        step_count (int): Total steps executed in graph.
        total_tokens (int): Cumulative LLM token count.
        total_cost_usd (float): Cumulative accrued cost in USD.
        requires_human_approval (bool): Flag indicating human gate required.
        approved (bool): Human sign-off status.
        action_executed (bool): Flag indicating outbound execution completed.
        action_result (Dict[str, Any]): Execution output payload and delivery receipt.
    """
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
