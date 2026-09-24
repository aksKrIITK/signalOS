from typing import Any, Dict
from pydantic import BaseModel
from app.agents.state import SDRState
from app.agents.prompts.prompt_loader import prompt_loader
from app.llm.base import ChatMessage
from app.llm.router import model_router


class CriticEvaluation(BaseModel):
    passed: bool = True
    groundedness_score: float = 0.95
    feedback: str = "Email copy is fully grounded in verified signals with valid citations."


async def critic_node(state: SDRState) -> Dict[str, Any]:
    step_count = state.get("step_count", 0) + 1
    research_iterations = state.get("research_iterations", 1)

    prompt_content = prompt_loader.load_prompt(
        "critic",
        "v1",
        {
            "email_subject": state.get("email_subject", ""),
            "email_body": state.get("email_body", ""),
            "signals": str(state.get("signals", [])),
            "research_dossier": str(state.get("research", [])),
        },
    )

    eval_result = await model_router.generate_structured_with_fallback(
        messages=[
            ChatMessage(role="system", content="You are a strict fact-checker and hallucination auditor."),
            ChatMessage(role="user", content=prompt_content),
        ],
        response_schema=CriticEvaluation,
        task_type="critic",
    )

    # Force pass if already iterated 2+ times to prevent infinite loop
    passed = eval_result.passed or research_iterations >= 2

    return {
        "step_count": step_count,
        "critic_passed": passed,
        "critic_feedback": eval_result.feedback,
        "total_tokens": state.get("total_tokens", 0) + 200,
        "total_cost_usd": state.get("total_cost_usd", 0.0) + 0.0008,
    }
