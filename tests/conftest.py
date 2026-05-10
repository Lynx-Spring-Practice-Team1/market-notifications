from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Base


@pytest.fixture
async def session_factory() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    yield factory

    await engine.dispose()


@pytest.fixture
async def session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as test_session:
        yield test_session


@pytest.fixture
def market_event_payload() -> dict:
    return {
        "event_id": "evt-001",
        "event_type": "SECTOR_SLUMP",
        "headline": "Regulatory concerns shake the Tech sector",
        "scope": "SECTOR",
        "target": "Tech",
        "magnitude": 1.8,
        "duration_ticks": 20,
        "market_time": "2024-03-15T11:00:00",
    }


@pytest.fixture
def market_event_envelope(market_event_payload: dict) -> dict:
    return {
        "type": "MARKET_EVENT",
        "payload": market_event_payload,
    }
