import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import get_settings
from app.db.session import async_session_factory
from app.kafka.producer import KafkaNotificationPublisher
from app.services.websocket import MarketEventWebsocketWorker


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    publisher: KafkaNotificationPublisher | None = None
    worker: MarketEventWebsocketWorker | None = None
    worker_task: asyncio.Task | None = None

    if settings.kafka_enabled:
        publisher = KafkaNotificationPublisher(settings)
        await publisher.start()

    if settings.market_ws_enabled:
        worker = MarketEventWebsocketWorker(
            async_session_factory,
            settings,
            publisher,
        )
        worker_task = asyncio.create_task(worker.run_forever())

    try:
        yield
    finally:
        if worker is not None:
            await worker.stop()
        if worker_task is not None:
            worker_task.cancel()
            with suppress(asyncio.CancelledError):
                await worker_task
        if publisher is not None:
            await publisher.stop()


app = FastAPI(title="Market Notifications Service", version="0.1.0", lifespan=lifespan)
app.include_router(router)
