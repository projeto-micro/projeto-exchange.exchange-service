import os
import time
from datetime import datetime
from typing import Dict, Tuple

import httpx
from fastapi import HTTPException, status

from schemas import ExchangeOut


CacheEntry = Tuple[float, ExchangeOut]

PROVIDER_URL = os.getenv(
    "EXCHANGE_PROVIDER_URL",
    "https://economia.awesomeapi.com.br/json/last/{from_currency}-{to_currency}",
)
REQUEST_TIMEOUT = float(os.getenv("EXCHANGE_REQUEST_TIMEOUT_SECONDS", "5"))
CACHE_TTL = int(os.getenv("EXCHANGE_CACHE_TTL_SECONDS", "60"))

_cache: Dict[str, CacheEntry] = {}


def _normalize(currency: str) -> str:
    value = currency.strip().upper()
    if len(value) != 3 or not value.isalpha():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Currency codes must use ISO-like 3-letter values",
        )
    return value


def _cache_key(from_currency: str, to_currency: str) -> str:
    return f"{from_currency}-{to_currency}"


def _read_cache(key: str) -> ExchangeOut | None:
    entry = _cache.get(key)
    if entry is None:
        return None

    created_at, value = entry
    if time.time() - created_at > CACHE_TTL:
        _cache.pop(key, None)
        return None

    return value


def _write_cache(key: str, value: ExchangeOut) -> ExchangeOut:
    _cache[key] = (time.time(), value)
    return value


async def get_exchange_rate(
    from_currency: str,
    to_currency: str,
    id_account: str,
) -> ExchangeOut:
    source = _normalize(from_currency)
    target = _normalize(to_currency)
    key = _cache_key(source, target)

    cached = _read_cache(key)
    if cached is not None:
        return cached.model_copy(update={"id_account": id_account})

    if source == target:
        return _write_cache(
            key,
            ExchangeOut(
                sell=1.0,
                buy=1.0,
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                id_account=id_account,
            ),
        )

    url = PROVIDER_URL.format(from_currency=source, to_currency=target)

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Exchange provider rejected {source}-{target}",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Exchange provider is unavailable",
        ) from exc

    payload = response.json()
    provider_key = f"{source}{target}"
    rate = payload.get(provider_key)
    if not rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exchange rate {source}-{target} was not found",
        )

    try:
        exchange = ExchangeOut(
            sell=float(rate["ask"]),
            buy=float(rate["bid"]),
            date=rate.get("create_date") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            id_account=id_account,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Exchange provider returned an invalid payload",
        ) from exc

    return _write_cache(key, exchange)
