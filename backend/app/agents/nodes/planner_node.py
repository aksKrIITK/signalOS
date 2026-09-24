from typing import Any, Dict
from app.agents.state import SDRState
from app.agents.policies.loop_guard import check_agent_limits
from app.agents.prompts.prompt_loader import prompt_loader
from app.llm.base import ChatMessage
from app.llm.router import model_router
from app.schemas.agent import ResearchPlan


async def planner_node(state: SDRState) -> Dict[str, Any]:
    step_count = state.get("step_count", 0) + 1
    total_cost = state.get("total_cost_usd", 0.0)
    tool_calls = state.get("tool_calls", [])
    check_agent_limits(step_count, len(tool_calls), total_cost)

    company = state.get("company", {})
    contact = state.get("contact", {})
    icp = state.get("icp", {})

    prompt_content = prompt_loader.load_prompt(
        "planner",
        "v1",
        {
            "company_name": company.get("name", "Target Account"),
            "domain": company.get("domain", "company.com"),
            "contact_name": f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip() or "Leadership",
            "job_title": contact.get("job_title", "CTO"),
            "icp_summary": str(icp),
        },
    )

    plan = await model_router.generate_structured_with_fallback(
        messages=[
            ChatMessage(role="system", content="You are a senior GTM strategist."),
            ChatMessage(role="user", content=prompt_content),
        ],
        response_schema=ResearchPlan,
        task_type="complex_reasoning",
    )

    return {
        "step_count": step_count,
        "research_plan": plan.model_dump(),
        "total_cost_usd": total_cost + 0.001,
        "total_tokens": state.get("total_tokens", 0) + 350,
    }
