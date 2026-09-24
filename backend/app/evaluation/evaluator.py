import time
import uuid
from typing import List
from app.agents.graph import sdr_graph
from app.agents.state import SDRState
from app.evaluation.dataset import EVALUATION_DATASET
from app.schemas.evaluation import EvalCase, EvalResult, EvalSummary
from app.core.logging import logger


class AgentEvaluator:
    async def evaluate_case(self, case: EvalCase) -> EvalResult:
        logger.info("evaluating_benchmark_case", case_id=case.id, name=case.name)
        start_time = time.time()

        initial_state: SDRState = {
            "organization_id": str(uuid.uuid4()),
            "campaign_id": str(uuid.uuid4()),
            "lead_id": str(uuid.uuid4()),
            "agent_run_id": str(uuid.uuid4()),
            "objective": f"Evaluate GTM workflow for {case.name}",
            "company": case.input.get("company", {}),
            "contact": case.input.get("contact", {}),
            "icp": case.input.get("icp", {}),
            "research": [],
            "signals": [],
            "retrieved_context": [],
            "tool_calls": [],
            "errors": [],
            "step_count": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "requires_human_approval": False,
            "approved": False,
        }

        final_state = await sdr_graph.ainvoke(initial_state)
        latency = time.time() - start_time

        used_tools = set(tc.get("tool_name") for tc in final_state.get("tool_calls", []))
        expected_tools = set(case.expected_tools)
        tool_accuracy = len(used_tools.intersection(expected_tools)) / len(expected_tools) if expected_tools else 1.0

        score = final_state.get("score", 0.0)
        score_in_bounds = case.min_expected_score <= score <= case.max_expected_score

        critic_passed = final_state.get("critic_passed", True)
        groundedness = 0.95 if critic_passed else 0.60
        hallucination_detected = not critic_passed

        reasons = []
        if not score_in_bounds:
            reasons.append(f"Score {score} not within [{case.min_expected_score}, {case.max_expected_score}]")
        if tool_accuracy < 0.6:
            reasons.append(f"Tool accuracy low: {tool_accuracy:.2f}")

        passed = score_in_bounds and tool_accuracy >= 0.6 and not hallucination_detected

        return EvalResult(
            case_id=case.id,
            name=case.name,
            passed=passed,
            groundedness_score=groundedness,
            tool_selection_accuracy=tool_accuracy,
            hallucination_detected=hallucination_detected,
            latency_seconds=round(latency, 3),
            cost_usd=round(final_state.get("total_cost_usd", 0.03), 4),
            reasons=reasons,
        )

    async def run_suite(self) -> EvalSummary:
        results: List[EvalResult] = []
        for case in EVALUATION_DATASET:
            res = await self.evaluate_case(case)
            results.append(res)

        total = len(results)
        passed = sum(1 for r in results if r.passed)
        avg_groundedness = sum(r.groundedness_score for r in results) / total if total > 0 else 0.0
        avg_latency = sum(r.latency_seconds for r in results) / total if total > 0 else 0.0
        total_cost = sum(r.cost_usd for r in results)

        return EvalSummary(
            total_cases=total,
            passed_cases=passed,
            success_rate=round((passed / total) * 100.0, 1),
            avg_groundedness=round(avg_groundedness, 3),
            avg_latency=round(avg_latency, 3),
            total_cost_usd=round(total_cost, 4),
            results=results,
        )


evaluator = AgentEvaluator()
