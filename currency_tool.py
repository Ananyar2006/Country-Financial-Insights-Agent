"""
Currency tools: map country -> currency and fetch FX rates.

External FX provider: https://currencyapi.com
You must set CURRENCY_API_KEY in your environment (e.g. .env).
"""

from __future__ import annotations

import os
from typing import Dict, Any

import requests


# Minimal but reliable mapping for common countries we care about.
COUNTRY_CURRENCY_MAP: Dict[str, Dict[str, str]] = {
    "india": {"code": "INR", "name": "Indian Rupee"},
    "united states": {"code": "USD", "name": "United States Dollar"},
    "united states of america": {"code": "USD", "name": "United States Dollar"},
    "usa": {"code": "USD", "name": "United States Dollar"},
    "japan": {"code": "JPY", "name": "Japanese Yen"},
    "united kingdom": {"code": "GBP", "name": "Pound Sterling"},
    "uk": {"code": "GBP", "name": "Pound Sterling"},
    "great britain": {"code": "GBP", "name": "Pound Sterling"},
    "south korea": {"code": "KRW", "name": "South Korean Won"},
    "republic of korea": {"code": "KRW", "name": "South Korean Won"},
    "korea, republic of": {"code": "KRW", "name": "South Korean Won"},
    "china": {"code": "CNY", "name": "Chinese Yuan Renminbi"},
    "people's republic of china": {"code": "CNY", "name": "Chinese Yuan Renminbi"},
}


def _normalize_country(country: str) -> str:
    return country.strip().lower()


def get_currency_for_country(country: str) -> Dict[str, Any]:
    """
    Determine the official currency for a country.

    Tries a local mapping first, then falls back to the Rest Countries API.
    Returns a dict with "country", "currency_name", and "currency_code".
    On failure, "error" will be set in the response.
    """
    country_norm = _normalize_country(country)

    # 1. Local mapping for reliability for common cases
    if country_norm in COUNTRY_CURRENCY_MAP:
        mapping = COUNTRY_CURRENCY_MAP[country_norm]
        return {
            "country": country.strip(),
            "currency_name": mapping["name"],
            "currency_code": mapping["code"],
            "source": "local_mapping",
        }

    # 2. Fallback to Rest Countries API (no key required)
    try:
        resp = requests.get(
            f"https://restcountries.com/v3.1/name/{country.strip()}",
            params={"fullText": "false", "fields": "currencies,name"},
            timeout=10,
        )
        if resp.status_code != 200:
            return {
                "country": country.strip(),
                "error": f"Failed to resolve currency via RestCountries (status {resp.status_code}).",
            }
        data = resp.json()
        if not data:
            return {
                "country": country.strip(),
                "error": "No country data returned from RestCountries.",
            }
        currencies = data[0].get("currencies") or {}
        if not currencies:
            return {
                "country": country.strip(),
                "error": "No currency information available for this country.",
            }
        # currencies is like {"INR": {"name": "Indian rupee", "symbol": "₹"}, ...}
        code, info = next(iter(currencies.items()))
        return {
            "country": country.strip(),
            "currency_name": info.get("name", ""),
            "currency_code": code,
            "source": "restcountries",
        }
    except Exception as exc:  # pragma: no cover - defensive
        return {
            "country": country.strip(),
            "error": f"Exception while resolving currency: {exc}",
        }


def get_exchange_rates_for_currency(currency_code: str) -> Dict[str, Any]:
    """
    Fetch exchange rates for 1 unit of the given currency against USD, INR, GBP, EUR.

    Uses https://currencyapi.com with the API key from CURRENCY_API_KEY.
    On failure, returns a dict with an "error" field.
    """
    base = currency_code.strip().upper()
    api_key = os.getenv("CURRENCY_API_KEY")
    target_currencies = ["USD", "INR", "GBP", "EUR"]

    if not api_key:
        return {
            "base_currency": base,
            "error": "CURRENCY_API_KEY is not set. Sign up at https://currencyapi.com/ and add it to your .env file.",
        }

    try:
        resp = requests.get(
            "https://api.currencyapi.com/v3/latest",
            params={
                "apikey": api_key,
                "base_currency": base,
                "currencies": ",".join(target_currencies),
            },
            timeout=10,
        )
        if resp.status_code != 200:
            return {
                "base_currency": base,
                "error": f"CurrencyAPI request failed with status {resp.status_code}: {resp.text[:200]}",
            }
        payload = resp.json()
        data = payload.get("data", {})
        rates: Dict[str, float] = {}
        for code in target_currencies:
            if code in data:
                # CurrencyAPI returns each entry with {"code": "USD", "value": 1.234, ...}
                try:
                    rates[code] = float(data[code].get("value", 0.0))
                except (TypeError, ValueError):
                    continue
        if not rates:
            return {
                "base_currency": base,
                "error": "No valid rates returned by CurrencyAPI.",
            }
        return {
            "base_currency": base,
            "rates": rates,
            "provider": "currencyapi.com",
        }
    except Exception as exc:  # pragma: no cover - defensive
        return {
            "base_currency": base,
            "error": f"Exception while calling CurrencyAPI: {exc}",
        }


__all__ = [
    "get_currency_for_country",
    "get_exchange_rates_for_currency",
]

