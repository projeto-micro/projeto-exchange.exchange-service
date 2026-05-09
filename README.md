# projeto-exchange.exchange-service

FastAPI microservice responsible for fetching currency exchange rates from a third-party provider.

## Overview

The service exposes a protected endpoint consumed through `gateway-service`.
The gateway validates the JWT cookie using `auth-service` and forwards the request with the `id-account` header.

```mermaid
flowchart LR
    Client --> Gateway[gateway-service]
    Gateway --> Exchange[exchange-service]
    Exchange --> Provider[AwesomeAPI]
```

## Endpoint

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/exchanges/{from}/{to}` | Required | Fetch the current exchange rate between two currencies |
| `GET` | `/health-check` | Internal | Liveness check |
| `GET` | `/info` | Internal | Basic service information |
| `GET` | `/metrics` | Internal | Prometheus metrics |

Example:

```http
GET /exchanges/USD/BRL
id-account: 0195ae95-5be7-7dd3-b35d-7a7d87c404fb
```

Response:

```json
{
  "sell": 5.71,
  "buy": 5.70,
  "date": "2026-05-09 14:23:42",
  "id-account": "0195ae95-5be7-7dd3-b35d-7a7d87c404fb"
}
```

## Bottlenecks

This service includes two bottleneck mitigations:

| Bottleneck | Implementation |
|---|---|
| Caching | In-memory TTL cache for repeated currency pairs |
| Observability | Prometheus metrics exposed at `/metrics` |

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `EXCHANGE_PROVIDER_URL` | AwesomeAPI URL template | Third-party exchange provider URL |
| `EXCHANGE_CACHE_TTL_SECONDS` | `60` | Cache duration per currency pair |
| `EXCHANGE_REQUEST_TIMEOUT_SECONDS` | `5` | Provider request timeout |

## Build & Run

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8080 --app-dir app
```

Or via Docker Compose from the parent `api/` directory:

```bash
docker compose up -d --build
```
