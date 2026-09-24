import pytest
import uuid
from app.agents.graph import sdr_graph
from app.agents.state import SDRState


@pytest.mark.asyncio
async def test_langgraph_full_sdr_execution():
    initial_state: SDRState = {
        "organization_id": str(uuid.uuid4()),
        "campaign_id": str(uuid.uuid4()),
        "lead_id": str(uuid.uuid4()),
        "agent_run_id": str(uuid.uuid4()),
        "objective": "Test GTM workflow execution",
        "company": {
            "name": "Finflow Systems",
            "domain": "finflow.io",
            "industry": "B2B SaaS",
            "employee_count": 180,
            "country": "India",
        },
        "contact": {
            "first_name": "Vikram",
            "last_name": "Sharma",
            "job_title": "VP Engineering",
            "email": "vikram.sharma@finflow.io",
            "linkedin_url": "https://linkedin.com/in/vikram",
        },
        "icp": {
            "industry": "B2B SaaS",
            "location": "India",
            "min_employees": 50,
            "max_employees": 500,
            "target_personas": ["VP Engineering", "CTO"],
        },
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

    assert final_state.get("score") is not None
    assert final_state.get("score") >= 75.0
    assert len(final_state.get("signals", [])) >= 2
    assert final_state.get("email_subject") != ""
    assert final_state.get("email_body") != ""
    assert len(final_state.get("tool_calls", [])) >= 2
    assert final_state.get("requires_human_approval") is True
