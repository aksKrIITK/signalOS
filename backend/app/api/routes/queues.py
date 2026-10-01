from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from app.api.dependencies import get_current_user as get_current_active_user
from app.core.config import settings
from app.workers.messaging import message_bus
from app.workers.messaging.schemas import DLQItem, JobExecutionTracker, QueueMetrics

router = APIRouter(prefix="/queues", tags=["Queue & Retry Management"])


class ReplayResponse(BaseModel):
    status: str
    dlq_id: str
    job_id: str
    topic: str


class PurgeResponse(BaseModel):
    purged_count: int
    topic: Optional[str] = None


@router.get("/status")
async def get_queue_status(current_user=Depends(get_current_active_user)):
    """Returns messaging queue configuration and active bus status."""
    return {
        "backend": settings.QUEUE_BACKEND,
        "kafka_bootstrap": settings.KAFKA_BOOTSTRAP_SERVERS,
        "max_retries": settings.MAX_JOB_RETRIES,
        "initial_backoff_seconds": settings.RETRY_INITIAL_DELAY_SECONDS,
        "max_backoff_seconds": settings.RETRY_MAX_DELAY_SECONDS,
        "jitter_enabled": settings.RETRY_JITTER,
        "dlq_enabled": settings.DLQ_ENABLED,
        "is_started": message_bus._started,
    }


@router.get("/jobs/{job_id}", response_model=JobExecutionTracker)
async def get_job_retry_state(
    job_id: str,
    current_user=Depends(get_current_active_user),
):
    """Retrieves detailed retry tracking state, attempt logs, and execution history for a job ID."""
    state = await message_bus.retry_tracker.get_job_state(job_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job tracking record for '{job_id}' not found.",
        )
    return state


@router.get("/dlq", response_model=List[DLQItem])
async def list_dlq_messages(
    topic: Optional[str] = Query(None, description="Filter DLQ items by topic name"),
    limit: int = Query(50, ge=1, le=500),
    current_user=Depends(get_current_active_user),
):
    """Lists unrecoverable failed messages stored in the Dead Letter Queue (DLQ)."""
    return await message_bus.dlq.list_dlq_items(topic=topic, limit=limit)


@router.post("/dlq/{dlq_id}/replay", response_model=ReplayResponse)
async def replay_dlq_message(
    dlq_id: str,
    current_user=Depends(get_current_active_user),
):
    """Replays a Dead Letter Queue item back onto its original topic for re-execution."""
    msg = await message_bus.dlq.replay_dlq_item(dlq_id, message_bus.producer)
    if not msg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"DLQ item '{dlq_id}' not found or could not be replayed.",
        )
    return ReplayResponse(
        status="REPLAYED",
        dlq_id=dlq_id,
        job_id=msg.job_id,
        topic=msg.topic,
    )


@router.delete("/dlq", response_model=PurgeResponse)
async def purge_dlq_messages(
    topic: Optional[str] = Query(None, description="Topic to purge from DLQ (purges all if omitted)"),
    current_user=Depends(get_current_active_user),
):
    """Purges items from the Dead Letter Queue."""
    count = await message_bus.dlq.purge(topic=topic)
    return PurgeResponse(purged_count=count, topic=topic)
