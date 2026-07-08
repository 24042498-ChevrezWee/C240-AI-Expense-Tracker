import os
from typing import Dict, Optional

import requests


DEFAULT_BASE_CURRENCY = "SGD"
_EXCHANGE_RATE_CACHE: Dict[str, float] = {}


def normalize_currency_code(currency_code: Optional[str]) -> str:
    if not currency_code:
        return DEFAULT_BASE_CURRENCY

    cleaned = str(currency_code).strip().upper()
    mapping = {
        "RM": "MYR",
        "S$": "SGD",
        "SGD": "SGD",
        "MYR": "MYR",
        "USD": "USD",
    }

    return mapping.get(cleaned, cleaned)


def _get_rate_from_api(base_currency: str, target_currency: str) -> Optional[float]:
    if base_currency == target_currency:
        return 1.0

    try:
        response = requests.get(
            "https://open.er-api.com/v6/latest/SGD",
            timeout=5,
        )
        response.raise_for_status()
        payload = response.json()
        rates = payload.get("rates") or {}
        if not rates:
            return None

        base_to_sgd = 1.0 / float(rates.get(base_currency, 0.0)) if base_currency != "SGD" else 1.0
        target_to_sgd = float(rates.get(target_currency, 0.0)) if target_currency != "SGD" else 1.0
        return base_to_sgd * target_to_sgd
    except Exception:
        return None


def get_exchange_rate(from_currency: Optional[str], to_currency: str = DEFAULT_BASE_CURRENCY) -> Optional[float]:
    source_currency = normalize_currency_code(from_currency)
    target_currency = normalize_currency_code(to_currency)

    if source_currency == target_currency:
        return 1.0

    cache_key = f"{source_currency}->{target_currency}"
    if cache_key in _EXCHANGE_RATE_CACHE:
        return _EXCHANGE_RATE_CACHE[cache_key]

    rate = _get_rate_from_api(source_currency, target_currency)
    if rate is None:
        return None

    _EXCHANGE_RATE_CACHE[cache_key] = rate
    return rate


def convert_amount_to_sgd(amount, currency_code: Optional[str]) -> Optional[float]:
    try:
        numeric_amount = float(amount)
    except (TypeError, ValueError):
        return None

    normalized_currency = normalize_currency_code(currency_code)
    if normalized_currency == DEFAULT_BASE_CURRENCY:
        return numeric_amount

    rate = get_exchange_rate(normalized_currency, DEFAULT_BASE_CURRENCY)
    if rate is None:
        return None

    return numeric_amount * rate
