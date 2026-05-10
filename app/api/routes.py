from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.events import MarketEventResponse
from app.services.market_events import MarketEventService

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "market-notifications"}


@router.get("/api/market/events", response_model=list[MarketEventResponse])
@router.get("/market/events", response_model=list[MarketEventResponse])
async def list_market_events(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    event_type: str | None = None,
    scope: str | None = None,
    target: str | None = None,
) -> list[MarketEventResponse]:
    service = MarketEventService(session)
    return await service.list_events(
        limit=limit,
        event_type=event_type,
        scope=scope,
        target=target,
    )


@router.get("/api/market/events/{event_id}", response_model=MarketEventResponse)
@router.get("/market/events/{event_id}", response_model=MarketEventResponse)
async def get_market_event(
    event_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MarketEventResponse:
    service = MarketEventService(session)
    event = await service.get_event(event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market event not found",
        )
    return event
