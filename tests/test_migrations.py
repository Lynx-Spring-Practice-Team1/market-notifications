from app.models import Base


def test_metadata_contains_market_events_table() -> None:
    assert {"market_events"}.issubset(Base.metadata.tables.keys())
