from fastapi import FastAPI, Header
from prometheus_fastapi_instrumentator import Instrumentator

from exchange_service import get_exchange_rate
from schemas import ExchangeOut


app = FastAPI(
    title="Exchange API",
    version="1.0.0",
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Exchange API"}


@app.get("/health-check")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/info")
async def info() -> dict[str, str]:
    return {
        "application": "exchange-service",
        "framework": "FastAPI",
        "status": "running",
    }


@app.get("/exchanges/{from_currency}/{to_currency}", response_model=ExchangeOut)
async def exchange(
    from_currency: str,
    to_currency: str,
    id_account: str = Header(..., alias="id-account"),
) -> ExchangeOut:
    return await get_exchange_rate(from_currency, to_currency, id_account)
