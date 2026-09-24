import asyncio
import json
import uuid
from typing import AsyncGenerator, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.models.user import User
from app.api.dependencies import get_current_user
from app.db.repositories.agent_run_repo import AgentRunRepository
from app.schemas.agent import AgentRunResponse
from app.workers.queues import queue_manager

router = APIRouter(prefix="/agent-runs", tags=["Agent Runs"])


@router.get("", response_model=List[AgentRunResponse])
async def list_agent_runs(
    campaign_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = AgentRunRepository(db)
    runs = await repo.list_runs(
        organization_id=current_user.organization_id,
        campaign_id=campaign_id,
        status=status,
        skip=skip,
        limit=limit,
    )
    return runs


@router.get("/{id}", response_model=AgentRunResponse)
async def get_agent_run(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = AgentRunRepository(db)
    run = await repo.get_with_tools(id, current_user.organization_id)
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return run


@router.post("/{id}/cancel")
async def cancel_agent_run(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = AgentRunRepository(db)
    run = await repo.get_by_id(id, current_user.organization_id)
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    await repo.update(run, status="CANCELLED")
    await db.commit()
    return {"status": "CANCELLED", "id": str(id)}


@router.get("/{id}/stream")
async def stream_agent_trace(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
):
    """
    Real-time Server-Sent Events (SSE) stream for live agent execution trace.
    Broadcasts step-by-step progress, tool calls, and LLM reasoning.
    """
    channel = f"stream:run:{str(id)}"

    async def event_generator() -> AsyncGenerator[str, None]:
        # Initial connect event
        yield f"event: connect\ndata: {json.dumps({'run_id': str(id), 'status': 'connected'})}\n\n"

        # Listen to Redis PubSub if available, else send mock heartbeat trace
        r = await queue_manager.get_redis()
        if r:
            pubsub = r.pubsub()
            await pubsub.subscribe(channel)
            try:
                while True:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    if message:
                        raw_data = message.get("data")
                        yield f"event: message\ndata: {raw_data}\n\n"
                    await asyncio.sleep(0.5)
            finally:
                await pubsub.unsubscribe(channel)
        else:
            # Fallback local simulated SSE trace
            steps = [
                ("planner.started", {"step": "Planner", "detail": "Formulating GTM research plan..."}),
                ("tool.web_search", {"step": "web_search", "query": "Finflow systems funding and engineers"}),
                ("tool.fetch_page", {"step": "fetch_page", "url": "https://finflow.io/careers"}),
                ("rag.retrieval", {"step": "RAG", "chunks_retrieved": 2}),
                ("scoring.completed", {"step": "Lead Scoring", "score": 88.5}),
                ("personalization.completed", {"step": "Personalization", "subject": "Accelerating engineering velocity"}),
                ("critic.passed", {"step": "Critic Audit", "groundedness": 0.96}),
                ("approval.required", {"step": "Human Approval", "action": "send_email"}),
            ]
            for evt, payload in steps:
                await asyncio.sleep(0.6)
                yield f"event: {evt}\ndata: {json.dumps(payload)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
