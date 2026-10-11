import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import redis.asyncio as redis
from app.core.config import settings
from app.core.logging import logger
from app.workers.messaging.interfaces import IRetryTracker
from app.workers.messaging.retry import format_exception_stack
from app.workers.messaging.schemas import JobExecutionTracker, JobState, RetryHistoryEntry


class RedisRetryTracker(IRetryTracker):
    """
    Production-grade Redis & DB Retry State Tracker implementing IRetryTracker.
    Maintains atomic job state, retry counters, attempt log history, and retry metrics.
    """

    def __init__(self, redis_url: str = settings.REDIS_URL):
        self.redis_url = redis_url
        self._redis: Optional[redis.Redis] = None
        self._connection_failed: bool = False
        self._memory_store: Dict[str, JobExecutionTracker] = {}

    async def get_redis(self) -> Optional[redis.Redis]:
        if self._connection_failed:
            return None
        if self._redis is None:
            try:
                self._redis = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=0.3,
                )
                await self._redis.ping()
            except Exception as e:
                logger.warning("redis_tracker_connection_failed_memory_fallback", error=str(e))
                self._connection_failed = True
                self._redis = None
        return self._redis

    async def record_attempt(
        self,
        job_id: str,
        topic: str,
        attempt: int,
        max_attempts: int,
        error: Optional[Exception] = None,
        backoff_seconds: float = 0.0,
        payload: Optional[Dict[str, Any]] = None,
    ) -> JobExecutionTracker:
        now_iso = datetime.now(timezone.utc).isoformat()

        # Build history entry if error occurred
        history_entry = None
        if error:
            history_entry = RetryHistoryEntry(
                attempt=attempt,
                timestamp=now_iso,
                error_type=error.__class__.__name__,
                error_message=str(error),
                backoff_seconds=backoff_seconds,
                stack_trace=format_exception_stack(error),
            )

        existing = await self.get_job_state(job_id)
        if existing:
            tracker = existing
            tracker.attempts = attempt
            tracker.last_attempt_at = now_iso
            tracker.state = JobState.RETRYING if error and attempt < max_attempts else JobState.PROCESSING
            if error:
                tracker.last_error = str(error)
                if history_entry:
                    tracker.history.append(history_entry)
        else:
            tracker = JobExecutionTracker(
                job_id=job_id,
                topic=topic,
                state=JobState.PROCESSING,
                attempts=attempt,
                max_attempts=max_attempts,
                first_attempt_at=now_iso,
                last_attempt_at=now_iso,
                last_error=str(error) if error else None,
                history=[history_entry] if history_entry else [],
                payload=payload or {},
            )

        if backoff_seconds > 0:
            next_retry_epoch = time.time() + backoff_seconds
            tracker.next_retry_at = datetime.fromtimestamp(next_retry_epoch, tz=timezone.utc).isoformat()

        # Save to Redis
        r = await self.get_redis()
        if r:
            try:
                key = f"job_tracker:{job_id}"
                await r.set(key, tracker.model_dump_json(), ex=172800)  # 48h TTL
                if backoff_seconds > 0:
                    # Record scheduled retry in sorted set
                    await r.zadd(f"delayed_retries:{topic}", {job_id: time.time() + backoff_seconds})
            except Exception as e:
                logger.warning("redis_tracker_save_failed", job_id=job_id, error=str(e))

        # Memory store fallback
        self._memory_store[job_id] = tracker
        return tracker

    async def record_success(self, job_id: str) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        tracker = await self.get_job_state(job_id)
        if tracker:
            tracker.state = JobState.COMPLETED
            tracker.last_attempt_at = now_iso
            tracker.next_retry_at = None

            r = await self.get_redis()
            if r:
                try:
                    await r.set(f"job_tracker:{job_id}", tracker.model_dump_json(), ex=172800)
                    # Remove from delayed retries if present
                    if tracker.topic:
                        await r.zrem(f"delayed_retries:{tracker.topic}", job_id)
                except Exception:
                    pass
            self._memory_store[job_id] = tracker

    async def record_dlq_failure(self, job_id: str, final_error: str) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        tracker = await self.get_job_state(job_id)
        if tracker:
            tracker.state = JobState.DLQ_FAILED
            tracker.last_attempt_at = now_iso
            tracker.last_error = final_error
            tracker.next_retry_at = None

            r = await self.get_redis()
            if r:
                try:
                    await r.set(f"job_tracker:{job_id}", tracker.model_dump_json(), ex=172800)
                    if tracker.topic:
                        await r.zrem(f"delayed_retries:{tracker.topic}", job_id)
                except Exception:
                    pass
            self._memory_store[job_id] = tracker

    async def get_job_state(self, job_id: str) -> Optional[JobExecutionTracker]:
        r = await self.get_redis()
        if r:
            try:
                raw = await r.get(f"job_tracker:{job_id}")
                if raw:
                    return JobExecutionTracker(**json.loads(raw))
            except Exception as e:
                logger.warning("redis_tracker_fetch_error", job_id=job_id, error=str(e))
        return self._memory_store.get(job_id)
