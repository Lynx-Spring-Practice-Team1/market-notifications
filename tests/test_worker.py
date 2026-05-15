import json

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.services.websocket import MarketEventWebsocketWorker


class FakePublisher:
    def __init__(self) -> None:
        self.events = []

    async def publish_market_event(self, event) -> None:
        self.events.append(event)


class FakeRelay:
    def __init__(self) -> None:
        self.broadcasts = []
        self.user_messages = []

    async def broadcast(self, message: str) -> None:
        self.broadcasts.append(message)

    async def send_to_user(self, user_id: str, message: str) -> None:
        self.user_messages.append((user_id, message))


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
async def test_worker_stores_publishes_and_relays_market_event(
    session_factory: async_sessionmaker[AsyncSession],
    market_event_envelope: dict,
) -> None:
    publisher = FakePublisher()
    relay = FakeRelay()
    worker = MarketEventWebsocketWorker(session_factory, publisher=publisher, relay=relay)

    handled = await worker.handle_message(json.dumps(market_event_envelope))

    assert handled is True
    assert len(publisher.events) == 1
    assert len(relay.broadcasts) == 1
    relayed = json.loads(relay.broadcasts[0])
    assert relayed["type"] == "MARKET_EVENT"
    assert relayed["payload"]["event_id"] == "evt-001"


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
async def test_worker_does_not_relay_duplicate_market_event(
    session_factory: async_sessionmaker[AsyncSession],
    market_event_envelope: dict,
) -> None:
    publisher = FakePublisher()
    relay = FakeRelay()
    worker = MarketEventWebsocketWorker(session_factory, publisher=publisher, relay=relay)

    assert await worker.handle_message(json.dumps(market_event_envelope)) is True
    assert await worker.handle_message(json.dumps(market_event_envelope)) is False

    assert len(publisher.events) == 1
    assert len(relay.broadcasts) == 1


@pytest.mark.asyncio
async def test_worker_ignores_non_market_event(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    publisher = FakePublisher()
    relay = FakeRelay()
    worker = MarketEventWebsocketWorker(session_factory, publisher=publisher, relay=relay)

    handled = await worker.handle_message(json.dumps({"type": "CONNECTED", "payload": {}}))

    assert handled is False
    assert publisher.events == []
    assert relay.broadcasts == []
    assert relay.user_messages == []


@pytest.mark.asyncio
async def test_worker_preserves_price_update_relay_behavior(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    relay = FakeRelay()
    worker = MarketEventWebsocketWorker(session_factory, relay=relay)
    message = json.dumps({"type": "PRICE_UPDATE", "payload": {"ticker": "ARKA", "price": 12.3}})

    handled = await worker.handle_message(message)

    assert handled is True
    assert relay.broadcasts == [message]


@pytest.mark.asyncio
async def test_worker_preserves_order_update_user_relay_behavior(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    relay = FakeRelay()
    worker = MarketEventWebsocketWorker(session_factory, relay=relay)
    message = json.dumps({
        "type": "ORDER_UPDATE",
        "payload": {"platform_user_id": "user-1", "status": "FILLED"},
    })

    handled = await worker.handle_message(message)

    assert handled is True
    assert relay.user_messages == [("user-1", message)]
