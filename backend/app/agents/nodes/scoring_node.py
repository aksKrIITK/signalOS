from typing import Any, Dict
from app.agents.state import SDRState
from app.services.scoring_service import scoring_engine


async def scoring_node(state: SDRState) -> Dict[str, Any]:
    """
    Computes deterministic and signal-based qualification scores for the lead.

    Evaluates company attributes, decision maker persona, and detected buying signals
    against campaign ICP criteria using the hybrid scoring engine.

    Args:
        state (SDRState): Current execution state containing company, contact, signals, and ICP.

    Returns:
        Dict[str, Any]: Updated state containing numerical score (0-100),
            qualification rationale reasons, and confidence metric.
    """
    step_count = state.get("step_count", 0) + 1
    company = state.get("company", {})
    contact = state.get("contact", {})
    signals = state.get("signals", [])
    icp = state.get("icp", {})

    breakdown = scoring_engine.calculate_score(
        company=company,
        contact=contact,
        detected_signals=signals,
        icp=icp,
    )

    return {
        "step_count": step_count,
        "score": breakdown.score,
        "score_reasons": breakdown.reasons,
        "score_confidence": breakdown.confidence,
    }
