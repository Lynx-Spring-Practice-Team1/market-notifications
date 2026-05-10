from collections.abc import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.session import get_session
from app.main import app
from app.schemas.events import MarketEventEnvelope
from app.services.market_events import MarketEventService


@pytest.fixture
async def client(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[TestClient, None]:
    async def override_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
async def stored_market_event(
    session_factory: async_sessionmaker[AsyncSession],
    market_event_envelope: dict,
) -> None:
    async with session_factory() as session:
        service = MarketEventService(session)
        await service.record_event(MarketEventEnvelope.model_validate(market_event_envelope))
        await session.commit()


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "market-notifications"}


@pytest.mark.usefixtures("stored_market_event")
def test_list_market_events(client: TestClient) -> None:
    response = client.get("/api/market/events", params={"event_type": "sector_slump"})

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["event_id"] == "evt-001"


@pytest.mark.usefixtures("stored_market_event")
def test_get_market_event(client: TestClient) -> None:
    response = client.get("/api/market/events/evt-001")

    assert response.status_code == 200
    assert response.json()["headline"] == "Regulatory concerns shake the Tech sector"


def test_get_market_event_not_found(client: TestClient) -> None:
    response = client.get("/api/market/events/missing")

    assert response.status_code == 404
