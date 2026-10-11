import json
import uuid
from typing import Any, List, Optional
import redis.asyncio as redis
from app.core.config import settings
from app.core.logging import logger
from app.workers.messaging.interfaces import IDeadLetterQueue, IMessageProducer
from app.workers.messaging.schemas import DLQItem, MessagePayload, RetryHistoryEntry


class RedisDeadLetterQueue(IDeadLetterQueue):
    """
    Production-grade Dead Letter Queue (DLQ) implementation fulfilling IDeadLetterQueue interface.
    Stores failed messages for inspection, alert notifications, and manual replaying.
    """

    def __init__(self, redis_url: str = settings.REDIS_URL):
        self.redis_url = redis_url
        self._redis: Optional[redis.Redis] = None
        self._connection_failed: bool = False
        self._memory_dlq: List[DLQItem] = []

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
                logger.warning("redis_dlq_connection_failed_memory_fallback", error=str(e))
                self._connection_failed = True
                self._redis = None
        return self._redis

    async def send_to_dlq(
        self,
        message: MessagePayload,
        final_error: Exception,
        history: List[RetryHistoryEntry],
    ) -> DLQItem:
        dlq_item = DLQItem(
            dlq_id=str(uuid.uuid4()),
            original_job_id=message.job_id,
            topic=message.topic,
            payload=message.payload,
            total_attempts=message.attempts,
            final_error=str(final_error),
            error_type=final_error.__class__.__name__,
            history=history,
        )

        logger.error(
            "message_sent_to_dlq",
            topic=message.topic,
            job_id=message.job_id,
            attempts=message.attempts,
            error=str(final_error),
        )

        r = await self.get_redis()
        if r:
            try:
                key = f"dlq:{message.topic}"
                item_json = dlq_item.model_dump_json()
                await r.rpush(key, item_json)
                await r.hset("dlq_index", dlq_item.dlq_id, item_json)
            except Exception as e:
                logger.error("redis_dlq_save_failed", job_id=message.job_id, error=str(e))
                self._connection_failed = True

        self._memory_dlq.append(dlq_item)
        return dlq_item

    async def list_dlq_items(self, topic: Optional[str] = None, limit: int = 50) -> List[DLQItem]:
        r = await self.get_redis()
        if r:
            try:
                if topic:
                    items_raw = await r.lrange(f"dlq:{topic}", 0, limit - 1)
                else:
                    items_raw = await r.hvals("dlq_index")
                    items_raw = items_raw[:limit]

                result = []
                for raw in items_raw:
                    result.append(DLQItem(**json.loads(raw)))
                return result
            except Exception as e:
                logger.warning("redis_dlq_list_failed", error=str(e))
                self._connection_failed = True

        if topic:
            return [item for item in self._memory_dlq if item.topic == topic][:limit]
        return self._memory_dlq[:limit]

    async def replay_dlq_item(self, dlq_id: str, producer: IMessageProducer) -> Optional[MessagePayload]:
        r = await self.get_redis()
        target_item: Optional[DLQItem] = None

        if r:
            try:
                raw = await r.hget("dlq_index", dlq_id)
                if raw:
                    target_item = DLQItem(**json.loads(raw))
                    await r.hdel("dlq_index", dlq_id)
                    await r.lrem(f"dlq:{target_item.topic}", 1, raw)
            except Exception as e:
                logger.warning("redis_dlq_replay_failed", dlq_id=dlq_id, error=str(e))

        if not target_item:
            for item in self._memory_dlq:
                if item.dlq_id == dlq_id:
                    target_item = item
                    self._memory_dlq.remove(item)
                    break

        if not target_item:
            logger.warning("dlq_item_not_found_for_replay", dlq_id=dlq_id)
            return None

        # Reset attempts counter and produce message back to original topic
        replayed_payload = dict(target_item.payload)
        replayed_payload["attempts"] = 0
        replayed_payload["replayed_from_dlq"] = True

        msg = await producer.produce(target_item.topic, replayed_payload, key=target_item.original_job_id)
        logger.info("dlq_item_replayed_successfully", dlq_id=dlq_id, topic=target_item.topic, job_id=msg.job_id)
        return msg

    async def purge(self, topic: Optional[str] = None) -> int:
        count = 0
        r = await self.get_redis()
        if r:
            try:
                if topic:
                    count = await r.llen(f"dlq:{topic}")
                    await r.delete(f"dlq:{topic}")
                else:
                    count = await r.hlen("dlq_index")
                    await r.delete("dlq_index")
            except Exception:
                pass

        if topic:
            self._memory_dlq = [item for item in self._memory_dlq if item.topic != topic]
        else:
            self._memory_dlq.clear()
        return count
