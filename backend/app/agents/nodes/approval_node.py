from typing import Any, Dict
from app.agents.state import SDRState


async def approval_node(state: SDRState) -> Dict[str, Any]:
    """
    Evaluates whether the generated outreach action requires human intervention.

    Args:
        state (SDRState): Current execution state of the SDR agent pipeline.

    Returns:
        Dict[str, Any]: State updates containing incremented step count and
            a boolean flag indicating if human approval is required.
    """
    step_count = state.get("step_count", 0) + 1
    # Check if human has already granted approval
    approved = state.get("approved", False)

    return {
        "step_count": step_count,
        "requires_human_approval": not approved,
    }


async def execution_node(state: SDRState) -> Dict[str, Any]:
    """
    Executes approved outreach actions (e.g., dispatching email) for the target lead.

    Args:
        state (SDRState): Current state containing contact details, target company,
            and approved email copy.

    Returns:
        Dict[str, Any]: Updated state with execution status and action results.
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
