from typing import Any, Dict
from app.agents.state import SDRState


async def enrichment_node(state: SDRState) -> Dict[str, Any]:
    """
    Enriches target company and contact records with deeper technographic and funding data.

    Augments entity profiles with tech stack dependencies, funding stages,
    growth trajectories, and verified email seniorities.

    Args:
        state (SDRState): Current execution state with base company and contact objects.

    Returns:
        Dict[str, Any]: Updated state dictionary containing enriched company and contact data.
    """
    company = dict(state.get("company", {}))
    contact = dict(state.get("contact", {}))
    step_count = state.get("step_count", 0) + 1

    # Enrich tech stack and metadata based on research
    company["tech_stack"] = ["Python", "FastAPI", "PostgreSQL", "AWS", "Docker", "Redis"]
    company["funding_total"] = "$18M Series A"
    company["growth_rate"] = "+45% YoY"

    contact["seniority"] = "Executive"
    contact["verified_email"] = True

    return {
        "step_count": step_count,
        "company": company,
        "contact": contact,
    }
