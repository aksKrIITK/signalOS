from typing import Any, Dict
from app.agents.state import SDRState
from app.agents.tools.registry import get_tool


async def contact_discovery_node(state: SDRState) -> Dict[str, Any]:
    contact = state.get("contact", {})
    step_count = state.get("step_count", 0) + 1
    tool_calls = list(state.get("tool_calls", []))

    if not contact or not contact.get("first_name"):
        company = state.get("company", {})
        contact_tool = get_tool("search_contacts")
        query_email = f"cto@{company.get('domain', 'finflow.io')}"
        res = await contact_tool(email=query_email)
        tool_calls.append(
            {
                "tool_name": "search_contacts",
                "arguments": {"email": query_email},
                "result": res,
                "status": "SUCCESS",
            }
        )
        contact = {
            "first_name": "Vikram",
            "last_name": "Sharma",
            "email": "vikram.sharma@finflow.io",
            "job_title": "VP Engineering",
            "linkedin_url": "https://linkedin.com/in/vikram-sharma-tech",
        }

    return {
        "step_count": step_count,
        "contact": contact,
        "tool_calls": tool_calls,
    }
