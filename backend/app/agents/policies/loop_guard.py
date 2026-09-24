from app.core.config import settings
from app.core.exceptions import AppError


class LimitExceededError(AppError):
    def __init__(self, message: str):
        super().__init__(code="LIMIT_EXCEEDED", message=message, status_code=400)


def check_agent_limits(
    step_count: int,
    tool_call_count: int,
    total_cost_usd: float,
    max_steps: int = settings.MAX_AGENT_STEPS,
    max_tool_calls: int = settings.MAX_TOOL_CALLS,
    max_cost_usd: float = settings.MAX_COST_USD,
) -> None:
    if step_count > max_steps:
        raise LimitExceededError(f"Agent exceeded maximum step limit ({step_count}/{max_steps})")
    if tool_call_count > max_tool_calls:
        raise LimitExceededError(f"Agent exceeded maximum tool call budget ({tool_call_count}/{max_tool_calls})")
    if total_cost_usd > max_cost_usd:
        raise LimitExceededError(f"Agent exceeded maximum cost budget (${total_cost_usd:.4f}/${max_cost_usd:.2f})")
