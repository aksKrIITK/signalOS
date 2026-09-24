from typing import Any, Dict
from app.agents.state import SDRState


async def approval_node(state: SDRState) -> Dict[str, Any]:
    step_count = state.get("step_count", 0) + 1
    # Check if human has already granted approval
    approved = state.get("approved", False)

    return {
        "step_count": step_count,
        "requires_human_approval": not approved,
    }


async def execution_node(state: SDRState) -> Dict[str, Any]:
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
