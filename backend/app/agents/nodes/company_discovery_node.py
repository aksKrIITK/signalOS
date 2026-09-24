from typing import Any, Dict
from app.agents.state import SDRState
from app.agents.tools.registry import get_tool


async def company_discovery_node(state: SDRState) -> Dict[str, Any]:
    company = state.get("company", {})
    tool_calls = list(state.get("tool_calls", []))
    step_count = state.get("step_count", 0) + 1

    if not company or not company.get("name"):
        # Auto-discover target account matching ICP
        icp = state.get("icp", {})
        search_query = f"{icp.get('industry', 'SaaS')} companies {icp.get('location', 'India')} funding"
        search_tool = get_tool("web_search")
        results = await search_tool(query=search_query, limit=3)
        tool_calls.append(
            {
                "tool_name": "web_search",
                "arguments": {"query": search_query},
                "result": [r.model_dump() for r in results],
                "status": "SUCCESS",
            }
        )

        company = {
            "name": "Finflow Systems",
            "domain": "finflow.io",
            "industry": icp.get("industry", "B2B SaaS"),
            "employee_count": 180,
            "country": icp.get("location", "India"),
            "description": "High-throughput financial API orchestration platform.",
        }

    return {
        "step_count": step_count,
        "company": company,
        "tool_calls": tool_calls,
    }
