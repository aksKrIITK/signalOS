from typing import Any, Callable, Dict
from app.agents.tools.fetch_page import fetch_page
from app.agents.tools.web_search import web_search
from app.agents.tools.crm_tool import MockCRMAdapter
from app.agents.tools.rag_tool import retrieve_knowledge
from app.core.exceptions import ToolExecutionError

crm_adapter = MockCRMAdapter()


async def search_company(domain: str) -> Dict[str, Any]:
    comps = await crm_adapter.search_companies(domain)
    return {"companies": [c.model_dump() for c in comps]}


async def search_contacts(email: str) -> Dict[str, Any]:
    conts = await crm_adapter.search_contacts(email)
    return {"contacts": [c.model_dump() for c in conts]}


async def query_crm(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
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
    if tool_name not in TOOLS:
        raise ToolExecutionError(f"Tool '{tool_name}' is not in the authorized tool allowlist")
    return TOOLS[tool_name]
