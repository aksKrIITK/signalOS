import asyncio
import signal
import sys
from app.core.config import settings
from app.core.logging import logger, setup_logging
from app.workers.messaging import message_bus
from app.workers.tasks.campaign_worker import handle_agent_run_consumer_task

setup_logging(debug=settings.DEBUG)


async def run_consumers():
    """
    Main background consumer daemon process.
    Listens to high-throughput queue topics (Kafka / Redis Streams / Memory)
    and dispatches tasks to handlers wrapped in exponential backoff retries and DLQ routing.
    """
    logger.info("starting_signalos_worker_daemon", backend=settings.QUEUE_BACKEND)

    # Initialize bus connection
    await message_bus.start()

    # Register subscription handlers
    await message_bus.subscribe(
        topic="agent.runs",
        handler=handle_agent_run_consumer_task,
        batch_size=5,
    )

    logger.info("consumer_subscriptions_registered_listening_for_jobs")

    stop_event = asyncio.Event()

    def _shutdown_signal(sig, frame):
        logger.info("shutdown_signal_received_stopping_workers", signal=sig)
        stop_event.set()

    # Register graceful shutdown signals if OS supports it
    if sys.platform != "win32":
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: stop_event.set())

    try:
        await stop_event.wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        logger.info("stopping_message_bus_consumers")
        await message_bus.stop()
        logger.info("worker_daemon_stopped_gracefully")


if __name__ == "__main__":
    try:
        asyncio.run(run_consumers())
    except (KeyboardInterrupt, SystemExit):
        pass
