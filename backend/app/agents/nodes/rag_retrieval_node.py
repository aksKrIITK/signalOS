import uuid
from typing import Any, Dict, List
from app.agents.state import SDRState
from app.agents.tools.registry import get_tool


async def rag_retrieval_node(state: SDRState) -> Dict[str, Any]:
    step_count = state.get("step_count", 0) + 1
    org_id_str = state.get("organization_id", str(uuid.uuid4()))
    org_id = uuid.UUID(org_id_str) if isinstance(org_id_str, str) else org_id_str

    company = state.get("company", {})
    signals = state.get("signals", [])
    query = f"GTM positioning for {company.get('industry', 'SaaS')} signals: " + " ".join(s.get("name", "") for s in signals)

    rag_tool = get_tool("retrieve_knowledge")
    snippets = await rag_tool(organization_id=org_id, query=query, top_k=2)

    tool_calls = list(state.get("tool_calls", []))
    tool_calls.append(
        {
            "tool_name": "retrieve_knowledge",
            "arguments": {"query": query, "top_k": 2},
            "result": [s.model_dump() for s in snippets],
            "status": "SUCCESS",
        }
    )

    return {
        "step_count": step_count,
        "retrieved_context": [s.model_dump() for s in snippets],
        "tool_calls": tool_calls,
    }
