from typing import Any, Callable, Dict
from app.agents.tools.fetch_page import fetch_page
from app.agents.tools.web_search import web_search
from app.agents.tools.crm_tool import MockCRMAdapter
from app.agents.tools.rag_tool import retrieve_knowledge
from app.core.exceptions import ToolExecutionError

crm_adapter = MockCRMAdapter()


async def search_company(domain: str) -> Dict[str, Any]:
    """
    Looks up company records in the CRM matching the specified domain name.

    Args:
        domain (str): Domain name of the target organization (e.g., 'finflow.io').

    Returns:
        Dict[str, Any]: Dictionary containing list of serialized CRM company records.
    """
    comps = await crm_adapter.search_companies(domain)
    return {"companies": [c.model_dump() for c in comps]}


async def search_contacts(email: str) -> Dict[str, Any]:
    """
    Queries CRM contacts matching the specified email address.

    Args:
        email (str): Target contact's email address.

    Returns:
        Dict[str, Any]: Dictionary containing list of serialized CRM contact objects.
    """
    conts = await crm_adapter.search_contacts(email)
    return {"contacts": [c.model_dump() for c in conts]}


async def query_crm(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes a CRM mutation or activity log action.

    Args:
        action (str): Operation to perform (e.g., 'log_call', 'update_stage').
        payload (Dict[str, Any]): Parameters and details associated with the activity.

    Returns:
        Dict[str, Any]: Result status and identifiers returned by the CRM adapter.
    """
    return await crm_adapter.create_activity("comp-default", action, payload)


# Explicit Tool Registry Allowlist
TOOLS: Dict[str, Callable] = {
    "web_search": web_search,
    "fetch_page": fetch_page,
    "search_company": search_company,
    "search_contacts": search_contacts,
    "query_crm": query_crm,
    "retrieve_knowledge": retrieve_knowledge,
}


def get_tool(tool_name: str) -> Callable:
    """
    Resolves an authorized tool callable from the security registry allowlist.

    Args:
        tool_name (str): Unique name of the tool (e.g., 'web_search', 'fetch_page').

    Returns:
        Callable: The verified async callable implementing the tool logic.

    Raises:
        ToolExecutionError: If the requested tool name is not in the allowlist.
    """
    if tool_name not in TOOLS:
        raise ToolExecutionError(f"Tool '{tool_name}' is not in the authorized tool allowlist")
    return TOOLS[tool_name]
