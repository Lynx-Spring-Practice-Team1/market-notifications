from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class MarketEventPayload(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    event_id: str = Field(min_length=1, max_length=128)
    event_type: str = Field(min_length=1, max_length=64)
    headline: str = Field(min_length=1)
    scope: str = Field(min_length=1, max_length=32)
    target: str | None = Field(default=None, max_length=128)
    magnitude: float
    duration_ticks: int = Field(ge=0)
    market_time: datetime

    @field_validator("event_type", "scope", mode="before")
    @classmethod
    def normalize_uppercase(cls, value: str) -> str:
        return value.upper() if isinstance(value, str) else value


class MarketEventEnvelope(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    type: str
    payload: MarketEventPayload

    @field_validator("type", mode="before")
    @classmethod
    def normalize_type(cls, value: str) -> str:
        return value.upper() if isinstance(value, str) else value

    @field_validator("type")
    @classmethod
    def require_market_event(cls, value: str) -> str:
        if value != "MARKET_EVENT":
            raise ValueError("event type must be MARKET_EVENT")
        return value


class MarketEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: str
    event_type: str
    headline: str
    scope: str
    target: str | None = None
    magnitude: float
    duration_ticks: int
    market_time: datetime
    received_at: datetime
    published_at: datetime | None = None

    @field_serializer("market_time", "received_at", "published_at")
    def serialize_datetimes(self, value: datetime | None) -> str | None:
        return value.isoformat() if value is not None else None
