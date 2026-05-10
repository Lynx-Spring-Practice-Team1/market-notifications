import json
from urllib.parse import parse_qs, urlsplit

from app.core.config import Settings
from app.services.websocket import (
    build_exchange_ws_url,
    market_events_subscription_payload,
    parse_market_event_message,
)


def test_build_exchange_ws_url_adds_credentials() -> None:
    settings = Settings(
        exchange_ws_url="ws://localhost:8080/ws?existing=true",
        exchange_ws_api_key="key",
        exchange_ws_api_secret="secret",
    )

    parsed = urlsplit(build_exchange_ws_url(settings))
    query = parse_qs(parsed.query)

    assert query["existing"] == ["true"]
    assert query["api_key"] == ["key"]
    assert query["api_secret"] == ["secret"]


def test_market_events_subscription_payload_matches_exchange_contract() -> None:
    assert market_events_subscription_payload() == {
        "type": "SUBSCRIBE",
        "payload": {"channel": "MARKET_EVENTS"},
    }


def test_parse_market_event_message_accepts_nested_json(market_event_envelope: dict) -> None:
    event = parse_market_event_message(json.dumps(market_event_envelope))

    assert event is not None
    assert event.type == "MARKET_EVENT"
    assert event.payload.event_id == "evt-001"


def test_parse_market_event_message_ignores_other_messages() -> None:
    event = parse_market_event_message(
        json.dumps({"type": "CONNECTED", "payload": {"platform_id": "platform-1"}}),
    )

    assert event is None
