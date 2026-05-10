# Market Notifications Service

FastAPI service for broker-platform market notifications.

It connects to the stock-exchange websocket, subscribes to `MARKET_EVENTS`, stores each
`MARKET_EVENT` payload in PostgreSQL, and publishes the original nested event envelope to Kafka
topic `notification.created`.

## Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8005
```

## Main Environment Variables

- `DATABASE_URL`
- `KAFKA_ENABLED`
- `KAFKA_BOOTSTRAP_SERVERS` or `KAFKA_BROKERS`
- `KAFKA_NOTIFICATION_TOPIC`
- `MARKET_WS_ENABLED`
- `EXCHANGE_WS_URL`
- `EXCHANGE_WS_API_KEY`
- `EXCHANGE_WS_API_SECRET`

## API

- `GET /health`
- `GET /api/market/events?limit=50&event_type=&scope=&target=`
- `GET /api/market/events/{event_id}`
