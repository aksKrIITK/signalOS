from typing import Any, Dict
from app.agents.state import SDRState
from app.agents.prompts.prompt_loader import prompt_loader
from app.llm.base import ChatMessage
from app.llm.router import model_router
from app.schemas.agent import PersonalizedEmail


async def personalization_node(state: SDRState) -> Dict[str, Any]:
    step_count = state.get("step_count", 0) + 1
    company = state.get("company", {})
    contact = state.get("contact", {})
    signals = state.get("signals", [])
    research = state.get("research", [])
    retrieved_context = state.get("retrieved_context", [])

    prompt_content = prompt_loader.load_prompt(
        "personalization",
        "v1",
        {
            "company_name": company.get("name", "Target Company"),
            "contact_name": f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip() or "Engineering Leader",
            "job_title": contact.get("job_title", "VP Engineering"),
            "signals": str([s.get("name") for s in signals]),
            "research_dossier": str([r.get("title") for r in research]),
            "retrieved_context": str([c.get("content") for c in retrieved_context]),
        },
    )

    email_obj = await model_router.generate_structured_with_fallback(
        messages=[
            ChatMessage(role="system", content="You are a senior GTM copywriter adhering strictly to verified facts."),
            ChatMessage(role="user", content=prompt_content),
        ],
        response_schema=PersonalizedEmail,
        task_type="personalization",
    )

    total_tokens = state.get("total_tokens", 0) + 420
    total_cost = state.get("total_cost_usd", 0.0) + 0.002

    return {
        "step_count": step_count,
        "email_subject": email_obj.subject,
        "email_body": email_obj.full_body,
        "evidence_claims": [c.model_dump() for c in email_obj.evidence_claims],
        "total_tokens": total_tokens,
        "total_cost_usd": total_cost,
    }
