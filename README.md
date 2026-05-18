# Market Notifications Service

Real-time market event processing and notification relay for the broker platform.

## Overview

Connects to an external exchange via WebSocket, records market events (SECTOR_SLUMP, etc.) to PostgreSQL, publishes them to Kafka, and relays price/order/market updates to connected frontend clients over WebSocket. Built with Python/FastAPI using async patterns throughout.

## Tech Stack

- **Python 3.12** + **FastAPI 0.115** + **uvicorn**
- **PostgreSQL 16** via SQLAlchemy 2.0 (asyncpg) + Alembic migrations
- **aiokafka 0.10** — Kafka producer
- **websockets 12.0** — exchange WebSocket client and client relay
- **Pydantic v2** + pydantic-settings
- **pytest** + pytest-asyncio + aiosqlite (testing)

## Project Structure

```
market-notifications/
├── app/
│   ├── main.py                  # FastAPI app, lifespan management
│   ├── api/
│   │   └── routes.py            # REST + WebSocket endpoints
│   ├── core/
│   │   └── config.py            # Pydantic settings
│   ├── db/
│   │   └── session.py           # SQLAlchemy async engine
│   ├── kafka/
│   │   └── producer.py          # Kafka event publisher
│   ├── models/
│   │   └── market_event.py      # MarketEvent ORM model
│   ├── schemas/
│   │   └── events.py            # Pydantic validation schemas
│   └── services/
│       ├── market_events.py     # DB operations (record/query events)
│       ├── relay.py             # WebSocket relay manager
│       └── websocket.py         # Exchange WebSocket worker
├── migrations/                  # Alembic migrations
├── tests/                       # pytest test suite
├── pyproject.toml
├── requirements.txt
├── docker-compose.yml
└── alembic.ini
```

## API Endpoints

### Market Events

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/market/events` | List events (filter by `event_type`, `scope`, `target`; `limit` 1-200) |
| `GET` | `/api/market/events/{event_id}` | Get single event |

### WebSocket

| Method | Path | Description |
|--------|------|-------------|
| `WS` | `/api/ws?token=<jwt>` | Real-time relay for PRICE_UPDATE, ORDER_UPDATE, MARKET_EVENT |

JWT token required. User ID extracted from `sub` claim. Price updates are broadcast to all; order updates are routed per user.

### Internal Admin

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/internal/admin/metrics` | Connected users count (`X-Internal-Token` required) |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | required | PostgreSQL async connection string |
| `KAFKA_ENABLED` | `false` | Enable Kafka publishing |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka broker |
| `KAFKA_NOTIFICATION_TOPIC` | `notification.created` | Target Kafka topic |
| `MARKET_WS_ENABLED` | `false` | Connect to exchange WebSocket |
| `EXCHANGE_WS_URL` | `ws://localhost:8080/ws` | Exchange WebSocket URL |
| `EXCHANGE_WS_API_KEY` | `test-api-key` | Exchange API key |
| `EXCHANGE_WS_API_SECRET` | `test-api-secret` | Exchange API secret |
| `PRICE_FEED_ALL_TICKERS` | `false` | Subscribe all tickers vs. filtered list |
| `EXCHANGE_WS_RECONNECT_SECONDS` | `5` | Reconnect delay on disconnect |
| `JWT_SECRET` | `change-me-in-production` | JWT validation secret |
| `INTERNAL_SERVICE_TOKEN` | `change-me-in-production` | Internal admin token |

## Getting Started

### Local Development

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8005
```

### Docker Compose (Full Stack)

```bash
docker-compose up
```

Starts PostgreSQL (5435), Redpanda (9092), and the service (8005).

### Tests

```bash
pytest
```

Uses in-memory SQLite — no external database needed.

## Event Flow

1. Exchange WebSocket sends `MARKET_EVENT`, `PRICE_FEED`, or `ORDER_UPDATES`
2. `MarketEventWebsocketWorker` parses and validates the envelope
3. `MarketEventService` persists the event to PostgreSQL
4. Event is relayed to connected WebSocket clients
5. Event is published to Kafka `notification.created` topic
6. `published_at` timestamp is recorded in the database

## Market Event Schema

```json
{
  "event_id": "evt-001",
  "event_type": "SECTOR_SLUMP",
  "headline": "Regulatory concerns shake the Tech sector",
  "scope": "SECTOR",
  "target": "Tech",
  "magnitude": 1.8,
  "duration_ticks": 20,
  "market_time": "2024-03-15T11:00:00"
}
```

Events are deduplicated by `event_id` (unique constraint).

## Database Schema

**`market_events` table:** `id`, `event_id` (unique), `event_type`, `headline`, `scope`, `target`, `magnitude`, `duration_ticks`, `market_time`, `raw_event` (JSON), `received_at`, `published_at`

## Deployment

GitHub Actions CI/CD pushes to GHCR on push to `main`:
```
ghcr.io/lynx-spring-practice-team1/market-notifications:latest
```
