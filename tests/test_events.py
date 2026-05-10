import pytest
from pydantic import ValidationError

from app.schemas.events import MarketEventEnvelope


def test_market_event_envelope_accepts_nested_payload(market_event_envelope: dict) -> None:
    event = MarketEventEnvelope.model_validate(market_event_envelope)

    assert event.type == "MARKET_EVENT"
    assert event.payload.event_id == "evt-001"
    assert event.payload.event_type == "SECTOR_SLUMP"
    assert event.payload.target == "Tech"
    assert event.payload.magnitude == 1.8


@pytest.mark.parametrize(
    "event_type,scope,target",
    [
        ("BULL_RUN", "MARKET", "ALL"),
        ("BEAR_CRASH", "MARKET", "ALL"),
        ("SECTOR_BOOM", "SECTOR", "Tech"),
        ("SECTOR_SLUMP", "SECTOR", "Tech"),
        ("STOCK_SHOCK", "STOCK", "AAPL"),
    ],
)
def test_market_event_envelope_accepts_expected_exchange_event_types(
    market_event_envelope: dict,
    event_type: str,
    scope: str,
    target: str,
) -> None:
    market_event_envelope["payload"]["event_type"] = event_type.lower()
    market_event_envelope["payload"]["scope"] = scope.lower()
    market_event_envelope["payload"]["target"] = target

    event = MarketEventEnvelope.model_validate(market_event_envelope)

    assert event.payload.event_type == event_type
    assert event.payload.scope == scope
    assert event.payload.target == target


def test_market_event_envelope_rejects_other_message_types(market_event_envelope: dict) -> None:
    market_event_envelope["type"] = "PRICE_UPDATE"

    with pytest.raises(ValidationError):
        MarketEventEnvelope.model_validate(market_event_envelope)


def test_market_event_envelope_rejects_missing_event_id(market_event_envelope: dict) -> None:
    market_event_envelope["payload"]["event_id"] = ""

    with pytest.raises(ValidationError):
        MarketEventEnvelope.model_validate(market_event_envelope)
