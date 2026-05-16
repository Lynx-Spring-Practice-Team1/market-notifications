import base64
import hashlib
import hmac
import json
import time
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_session
from app.schemas.events import MarketEventResponse
from app.services.market_events import MarketEventService
from app.services.relay import relay_manager

router = APIRouter()


class AdminConnectionMetrics(BaseModel):
    connected_users: int
    total_connections: int
    connected_user_ids: list[str] = Field(default_factory=list)


def _b64decode(s: str) -> bytes:
    s += "=" * (4 - len(s) % 4)
    return base64.urlsafe_b64decode(s)


def _verify_jwt(token: str, secret: str) -> dict:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("malformed token")
    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode()
    expected = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, _b64decode(sig_b64)):
        raise ValueError("invalid signature")
    payload = json.loads(_b64decode(payload_b64))
    exp = payload.get("exp")
    if exp and time.time() > exp:
        raise ValueError("token expired")
    return payload


def require_internal_token(
    x_internal_token: Annotated[str | None, Header(alias="X-Internal-Token")] = None,
) -> None:
    if x_internal_token != get_settings().internal_service_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid internal token")


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "market-notifications"}


@router.websocket("/api/ws")
async def ws_relay(websocket: WebSocket, token: str = Query(...)):
    settings = get_settings()
    try:
        payload = _verify_jwt(token, settings.jwt_secret)
        user_id = str(payload.get("sub", ""))
        if not user_id:
            raise ValueError("missing sub claim")
    except Exception:
        await websocket.close(code=4001)
        return

    await websocket.accept()
    await relay_manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await relay_manager.disconnect(user_id, websocket)


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


@router.get("/internal/admin/metrics", response_model=AdminConnectionMetrics)
async def get_admin_metrics(
    _: Annotated[None, Depends(require_internal_token)],
) -> dict[str, int | list[str]]:
    return await relay_manager.metrics()
