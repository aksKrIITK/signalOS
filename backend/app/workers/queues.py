import asyncio
import json
import uuid
from typing import Any, Callable, Dict, Optional
import redis.asyncio as redis
from app.core.config import settings
from app.core.logging import logger


class QueueManager:
    def __init__(self):
        self._redis: Optional[redis.Redis] = None

    async def get_redis(self) -> redis.Redis:
        if self._redis is None:
            try:
                self._redis = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=3,
                )
            except Exception as e:
                logger.warning("redis_connection_failed_using_mock", error=str(e))
                self._redis = None
        return self._redis

    async def enqueue(self, queue_name: str, payload: Dict[str, Any], job_id: Optional[str] = None) -> str:
        job_id = job_id or str(uuid.uuid4())
        message = json.dumps({"job_id": job_id, "payload": payload, "attempts": 0})
        
        r = await self.get_redis()
        if r:
            try:
                await r.rpush(f"queue:{queue_name}", message)
                await r.set(f"job:{job_id}:status", "QUEUED", ex=86400)
            except Exception as e:
                logger.warning("redis_enqueue_fallback", error=str(e))
        return job_id

    async def dequeue(self, queue_name: str, timeout_seconds: int = 2) -> Optional[Dict[str, Any]]:
        r = await self.get_redis()
        if not r:
            return None
        try:
            item = await r.blpop(f"queue:{queue_name}", timeout=timeout_seconds)
            if item:
                _, data = item
                return json.loads(data)
        except Exception as e:
            logger.warning("redis_dequeue_error", error=str(e))
        return None

    async def set_job_status(self, job_id: str, status: str, result: Optional[Dict[str, Any]] = None) -> None:
        r = await self.get_redis()
        if r:
            try:
                await r.set(f"job:{job_id}:status", status, ex=86400)
                if result:
                    await r.set(f"job:{job_id}:result", json.dumps(result), ex=86400)
            except Exception:
                pass

    async def publish_event(self, channel: str, event_type: str, data: Dict[str, Any]) -> None:
        r = await self.get_redis()
        if r:
            try:
                payload = json.dumps({"event": event_type, "data": data})
                await r.publish(channel, payload)
            except Exception:
                pass


queue_manager = QueueManager()
