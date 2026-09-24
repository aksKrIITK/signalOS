from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class EvalCase(BaseModel):
    id: str
    name: str
    input: Dict[str, Any]
    expected_tools: List[str]
    expected_signals: List[str]
    min_expected_score: float
    max_expected_score: float


class EvalResult(BaseModel):
    case_id: str
    name: str
    passed: bool
    groundedness_score: float
    tool_selection_accuracy: float
    hallucination_detected: bool
    latency_seconds: float
    cost_usd: float
    reasons: List[str] = []


class EvalSummary(BaseModel):
    total_cases: int
    passed_cases: int
    success_rate: float
    avg_groundedness: float
    avg_latency: float
    total_cost_usd: float
    results: List[EvalResult]
