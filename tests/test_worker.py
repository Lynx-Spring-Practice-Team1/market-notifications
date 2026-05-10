import json

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.services.websocket import MarketEventWebsocketWorker


class FakePublisher:
    def __init__(self) -> None:
        self.events = []

    async def publish_market_event(self, event) -> None:
        self.events.append(event)


@pytest.mark.asyncio
async def test_worker_stores_and_publishes_market_event(
    session_factory: async_sessionmaker[AsyncSession],
    market_event_envelope: dict,
) -> None:
    publisher = FakePublisher()
    worker = MarketEventWebsocketWorker(session_factory, publisher=publisher)

    handled = await worker.handle_message(json.dumps(market_event_envelope))

    assert handled is True
    assert len(publisher.events) == 1
    assert publisher.events[0].payload.event_id == "evt-001"


@pytest.mark.asyncio
async def test_worker_does_not_publish_duplicate_event(
    session_factory: async_sessionmaker[AsyncSession],
    market_event_envelope: dict,
) -> None:
    publisher = FakePublisher()
    worker = MarketEventWebsocketWorker(session_factory, publisher=publisher)

    assert await worker.handle_message(json.dumps(market_event_envelope)) is True
    assert await worker.handle_message(json.dumps(market_event_envelope)) is False

    assert len(publisher.events) == 1


@pytest.mark.asyncio
async def test_worker_ignores_non_market_event(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    publisher = FakePublisher()
    worker = MarketEventWebsocketWorker(session_factory, publisher=publisher)

    handled = await worker.handle_message(json.dumps({"type": "CONNECTED", "payload": {}}))

    assert handled is False
    assert publisher.events == []
