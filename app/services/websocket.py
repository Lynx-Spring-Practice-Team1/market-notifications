import asyncio
import json
import logging
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings
from app.kafka.producer import KafkaNotificationPublisher
from app.schemas.events import MarketEventEnvelope
from app.services.market_events import MarketEventService

logger = logging.getLogger(__name__)


class MarketEventWebsocketWorker:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        settings: Settings | None = None,
        publisher: KafkaNotificationPublisher | None = None,
        relay=None,  # RelayManager | None — imported at runtime to avoid circular deps
    ) -> None:
        self.session_factory = session_factory
        self.settings = settings or get_settings()
        self.publisher = publisher
        self.relay = relay
        self._stop = asyncio.Event()

    async def stop(self) -> None:
        self._stop.set()

    async def run_forever(self) -> None:
        url = build_exchange_ws_url(self.settings)
        if not url:
            logger.warning("Exchange websocket URL is not configured")
            return

        import websockets

        while not self._stop.is_set():
            try:
                async with websockets.connect(url) as websocket:
                    await websocket.send(json.dumps(market_events_subscription_payload()))
                    if self.relay is not None:
                        await websocket.send(json.dumps({
                            "type": "SUBSCRIBE",
                            "payload": {"channel": "PRICE_FEED", "tickers": self.settings.tickers},
                        }))
                        await websocket.send(json.dumps({
                            "type": "SUBSCRIBE",
                            "payload": {"channel": "ORDER_UPDATES"},
                        }))
                    logger.info("Subscribed to exchange channels")

                    while not self._stop.is_set():
                        message = await websocket.recv()
                        await self.handle_message(message)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                if not self._stop.is_set():
                    logger.warning(
                        "Exchange websocket disconnected: %s; reconnecting in %ss",
                        exc,
                        self._reconnect_seconds(),
                    )
                    await asyncio.sleep(self._reconnect_seconds())

    async def handle_message(self, message: str | bytes) -> bool:
        raw = message if isinstance(message, str) else message.decode()

        try:
            msg = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return False

        msg_type = msg.get("type")

        if self.relay is not None:
            if msg_type == "PRICE_UPDATE":
                await self.relay.broadcast(raw)
                return True

            if msg_type == "ORDER_UPDATE":
                payload = msg.get("payload", {})
                user_id = str(payload.get("platform_user_id", ""))
                if user_id:
                    await self.relay.send_to_user(user_id, raw)
                else:
                    await self.relay.broadcast(raw)
                return True

        envelope = parse_market_event_message(raw)
        if envelope is None:
            return False

        async with self.session_factory() as session:
            service = MarketEventService(session)
            async with session.begin():
                result = await service.record_event(envelope)

            if not result.created:
                return False

            if self.relay is not None:
                await self.relay.broadcast(envelope.model_dump_json())

            if self.publisher is None:
                return True

            try:
                await self.publisher.publish_market_event(envelope)
            except Exception:
                logger.exception("Failed to publish market event %s", envelope.payload.event_id)
                return True

            async with session.begin():
                await service.mark_published(result.event)
            return True

    def _reconnect_seconds(self) -> int:
        return max(1, self.settings.exchange_ws_reconnect_seconds)


def build_exchange_ws_url(settings: Settings) -> str | None:
    if not settings.exchange_ws_url:
        return None

    url_parts = urlsplit(settings.exchange_ws_url)
    query = dict(parse_qsl(url_parts.query, keep_blank_values=True))
    if settings.exchange_ws_api_key:
        query["api_key"] = settings.exchange_ws_api_key
    if settings.exchange_ws_api_secret:
        query["api_secret"] = settings.exchange_ws_api_secret
    return urlunsplit(url_parts._replace(query=urlencode(query)))


def market_events_subscription_payload() -> dict[str, object]:
    return {
        "type": "SUBSCRIBE",
        "payload": {
            "channel": "MARKET_EVENTS",
        },
    }


def parse_market_event_message(message: str | bytes) -> MarketEventEnvelope | None:
    try:
        payload = json.loads(message)
    except (json.JSONDecodeError, TypeError, UnicodeDecodeError):
        return None

    try:
        return MarketEventEnvelope.model_validate(payload)
    except ValidationError:
        return None
