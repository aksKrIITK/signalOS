from typing import Any, Dict, List
from app.agents.state import SDRState
from app.agents.tools.registry import get_tool
from app.core.logging import logger


async def research_node(state: SDRState) -> Dict[str, Any]:
    company = state.get("company", {})
    tool_calls = list(state.get("tool_calls", []))
    step_count = state.get("step_count", 0) + 1
    research_items: List[Dict[str, Any]] = list(state.get("research", []))

    query = f"{company.get('name', 'Finflow')} funding news tech stack engineers"
    search_tool = get_tool("web_search")
    fetch_tool = get_tool("fetch_page")

    search_res = await search_tool(query=query, limit=3)
    tool_calls.append(
        {
            "tool_name": "web_search",
            "arguments": {"query": query},
            "result": [r.model_dump() for r in search_res],
            "status": "SUCCESS",
        }
    )

    for item in search_res:
        research_items.append(
            {
                "title": item.title,
                "url": item.url,
                "snippet": item.snippet,
                "source": item.source,
                "published_at": item.published_at,
            }
        )

    # Fetch top page with SSRF protection
    if search_res:
        top_url = search_res[0].url
        page_res = await fetch_tool(url=top_url)
        tool_calls.append(
            {
                "tool_name": "fetch_page",
                "arguments": {"url": top_url},
                "result": {"title": page_res.title, "length": len(page_res.main_content)},
                "status": "SUCCESS",
            }
        )
        research_items.append(
            {
                "title": page_res.title,
                "url": page_res.url,
                "snippet": page_res.main_content[:300],
                "source": "Web Extraction",
            }
        )

    return {
        "step_count": step_count,
        "research": research_items,
        "tool_calls": tool_calls,
        "research_iterations": state.get("research_iterations", 0) + 1,
    }
