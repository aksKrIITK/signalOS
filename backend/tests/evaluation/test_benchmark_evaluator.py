import pytest
from app.evaluation.evaluator import evaluator


@pytest.mark.asyncio
async def test_evaluation_benchmark_suite():
    summary = await evaluator.run_suite()

    assert summary.total_cases >= 3
    assert summary.success_rate >= 66.0
    assert summary.avg_groundedness >= 0.85
    assert summary.total_cost_usd > 0.0
