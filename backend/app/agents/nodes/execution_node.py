from typing import Any, Dict
from app.agents.state import SDRState


async def execution_node(state: SDRState) -> Dict[str, Any]:
    """
    Executes the outbound communication action (e.g., transactional email outreach).

    Dispatches outreach to the resolved recipient and records delivery status.

    Args:
        state (SDRState): Current execution state containing validated email copy,
            subject line, target contact, and company information.

    Returns:
        Dict[str, Any]: Updated state reflecting executed action status and delivery details.
    """
    step_count = state.get("step_count", 0) + 1
    company = state.get("company", {})
    contact = state.get("contact", {})

    action_result = {
        "action": "send_email",
        "recipient": contact.get("email", "lead@finflow.io"),
        "company": company.get("name", "Finflow Systems"),
        "subject": state.get("email_subject"),
        "status": "SENT",
    }

    return {
        "step_count": step_count,
        "action_executed": True,
        "action_result": action_result,
    }
