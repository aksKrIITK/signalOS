import asyncio
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import AsyncSessionLocal
from app.db.models.agent_run import AgentRun, AgentRunStatus, ToolCall
from app.db.repositories.agent_run_repo import AgentRunRepository
from app.db.repositories.lead_repo import LeadRepository
from app.agents.graph import sdr_graph
from app.agents.state import SDRState
from app.workers.queues import queue_manager
from app.core.logging import logger


async def execute_agent_pipeline(
    organization_id: uuid.UUID,
    campaign_id: Optional[uuid.UUID] = None,
    lead_id: Optional[uuid.UUID] = None,
    icp: Optional[Dict[str, Any]] = None,
    lead_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Executes LangGraph SDR pipeline for a lead, records run & tool calls durably in PostgreSQL,
    and publishes real-time SSE execution events.
    """
    async with AsyncSessionLocal() as db:
        agent_run_repo = AgentRunRepository(db)
        lead_repo = LeadRepository(db)

        # 1. Create initial AgentRun record
        run = await agent_run_repo.create(
            organization_id=organization_id,
            campaign_id=campaign_id,
            lead_id=lead_id,
            agent_type="sdr_pipeline",
            status=AgentRunStatus.RUNNING,
            input_json={"icp": icp or {}, "lead": lead_data or {}},
            output_json={},
            started_at=datetime.now(timezone.utc),
        )
        await db.commit()

        channel = f"stream:run:{str(run.id)}"
        await queue_manager.publish_event(
            channel, "agent.started", {"run_id": str(run.id), "status": "RUNNING"}
        )

        initial_state: SDRState = {
            "organization_id": str(organization_id),
            "campaign_id": str(campaign_id) if campaign_id else "",
            "lead_id": str(lead_id) if lead_id else "",
            "agent_run_id": str(run.id),
            "objective": "Autonomous GTM prospect research, scoring, and personalized outreach",
            "company": lead_data.get("company", {}) if lead_data else {},
            "contact": lead_data.get("contact", {}) if lead_data else {},
            "icp": icp or {},
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

        try:
            # Stream execution through LangGraph
            final_state = await sdr_graph.ainvoke(initial_state)

            # Record tool calls in DB
            for tc in final_state.get("tool_calls", []):
                tool_call = ToolCall(
                    agent_run_id=run.id,
                    tool_name=tc.get("tool_name", "unknown"),
                    arguments=tc.get("arguments", {}),
                    result=tc.get("result", {}) if isinstance(tc.get("result"), dict) else {"data": tc.get("result")},
                    status=tc.get("status", "SUCCESS"),
                    latency_ms=tc.get("latency_ms", 120),
                )
                db.add(tool_call)

            status = AgentRunStatus.WAITING_APPROVAL if final_state.get("requires_human_approval") else AgentRunStatus.COMPLETED

            # Update lead score if lead exists
            if lead_id:
                lead = await lead_repo.get_by_id(lead_id, organization_id)
                if lead:
                    await lead_repo.update(
                        lead,
                        score=final_state.get("score"),
                        score_reason={
                            "reasons": final_state.get("score_reasons", []),
                            "signals": [s.get("name") for s in final_state.get("signals", [])],
                            "confidence": final_state.get("score_confidence", 0.9),
                        },
                        status="QUALIFIED" if (final_state.get("score") or 0) >= 70 else "RESEARCHING",
                    )

            output_summary = {
                "score": final_state.get("score"),
                "score_reasons": final_state.get("score_reasons"),
                "signals": final_state.get("signals"),
                "email_subject": final_state.get("email_subject"),
                "email_body": final_state.get("email_body"),
                "evidence_claims": final_state.get("evidence_claims"),
                "critic_passed": final_state.get("critic_passed"),
                "requires_approval": final_state.get("requires_human_approval"),
            }

            await agent_run_repo.update(
                run,
                status=status,
                output_json=output_summary,
                model="gpt-4o",
                input_tokens=final_state.get("total_tokens", 1200),
                output_tokens=final_state.get("total_tokens", 800) // 2,
                cost_usd=final_state.get("total_cost_usd", 0.035),
                completed_at=datetime.now(timezone.utc),
            )
            await db.commit()

            await queue_manager.publish_event(
                channel, "agent.completed", {"run_id": str(run.id), "status": status, "output": output_summary}
            )

            return output_summary

        except Exception as e:
            logger.error("agent_execution_failed", run_id=str(run.id), error=str(e))
            await agent_run_repo.update(
                run,
                status=AgentRunStatus.FAILED,
                error=str(e),
                completed_at=datetime.now(timezone.utc),
            )
            await db.commit()
            await queue_manager.publish_event(
                channel, "agent.failed", {"run_id": str(run.id), "error": str(e)}
            )
            raise e
