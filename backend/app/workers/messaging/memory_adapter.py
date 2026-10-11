import asyncio
import json
import uuid
from typing import Any, Callable, Coroutine, Dict, List, Optional
from app.core.logging import logger
from app.workers.messaging.interfaces import IMessageConsumer, IMessageProducer
from app.workers.messaging.schemas import MessagePayload


class MemoryProducerAdapter(IMessageProducer):
    """In-Memory Producer Implementation for testing and lightweight local execution."""

    def __init__(self, queues: Optional[Dict[str, asyncio.Queue]] = None):
        self.queues: Dict[str, asyncio.Queue] = queues if queues is not None else {}
        self._running = False

    async def start(self) -> None:
        self._running = True

    async def stop(self) -> None:
        self._running = False

    def get_queue(self, topic: str) -> asyncio.Queue:
        if topic not in self.queues:
            self.queues[topic] = asyncio.Queue()
        return self.queues[topic]

    async def produce(self, topic: str, payload: Dict[str, Any], key: Optional[str] = None) -> MessagePayload:
        job_id = payload.get("job_id", str(uuid.uuid4()))
        message = MessagePayload(
            job_id=job_id,
            topic=topic,
            payload=payload,
            attempts=payload.get("attempts", 0),
            max_attempts=payload.get("max_attempts", 3),
        )
        queue = self.get_queue(topic)
        await queue.put(message)
        logger.debug("memory_produced_message", topic=topic, job_id=job_id)
        return message


class MemoryConsumerAdapter(IMessageConsumer):
    """In-Memory Consumer Implementation for testing and local execution."""

    def __init__(self, queues: Dict[str, asyncio.Queue]):
        self.queues = queues
        self._running = False
        self._tasks: List[asyncio.Task] = []

    async def start(self) -> None:
        self._running = True

    async def stop(self) -> None:
        self._running = False
        for task in self._tasks:
            task.cancel()

    async def consume(
        self,
        topic: str,
        handler: Callable[[MessagePayload], Coroutine[Any, Any, None]],
        batch_size: int = 1,
    ) -> None:
        if topic not in self.queues:
            self.queues[topic] = asyncio.Queue()
        queue = self.queues[topic]

        async def _consumer_loop():
            while self._running:
                try:
                    message: MessagePayload = await asyncio.wait_for(queue.get(), timeout=0.5)
                    try:
                        await handler(message)
                    except Exception as exc:
                        logger.error("memory_consumer_handler_error", topic=topic, job_id=message.job_id, error=str(exc))
                    finally:
                        queue.task_done()
                except asyncio.TimeoutError:
                    continue
                except asyncio.CancelledError:
                    break

        task = asyncio.create_task(_consumer_loop())
        self._tasks.append(task)
