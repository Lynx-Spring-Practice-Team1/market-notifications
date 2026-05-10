from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = "market-notifications"
    environment: str = "local"
    database_url: str = (
        "postgresql+asyncpg://market_notifications:market_notifications"
        "@localhost:5435/market_notifications_db"
    )

    kafka_enabled: bool = False
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        validation_alias=AliasChoices("KAFKA_BOOTSTRAP_SERVERS", "KAFKA_BROKERS"),
    )
    kafka_notification_topic: str = Field(
        default="notification.created",
        validation_alias=AliasChoices("KAFKA_NOTIFICATION_TOPIC", "NOTIFICATION_CREATED_TOPIC"),
    )

    market_ws_enabled: bool = False
    exchange_ws_url: str | None = Field(default="ws://localhost:8080/ws")
    exchange_ws_api_key: str | None = Field(default="test-api-key")
    exchange_ws_api_secret: str | None = Field(default="test-api-secret")
    exchange_ws_reconnect_seconds: int = 5


@lru_cache
def get_settings() -> Settings:
    return Settings()
