"""
Stock tools: map country -> major exchanges/indices and fetch latest index values.

Index price data provider: Yahoo Finance via the `yfinance` Python package.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Any

import yfinance as yf


@dataclass
class StockIndex:
    symbol: str
    name: str


@dataclass
class StockExchange:
    name: str
    city: str
    country: str
    headquarters_address: str
    indices: List[StockIndex]


# Hand-curated coverage for the required countries.
COUNTRY_STOCK_PROFILE: Dict[str, List[StockExchange]] = {
    "india": [
        StockExchange(
            name="National Stock Exchange of India (NSE)",
            city="Mumbai",
            country="India",
            headquarters_address="Exchange Plaza, Bandra Kurla Complex, Bandra East, Mumbai, Maharashtra 400051, India",
            indices=[
                StockIndex(symbol="^NSEI", name="Nifty 50"),
                StockIndex(symbol="^CNX100", name="Nifty 100"),
            ],
        ),
        StockExchange(
            name="Bombay Stock Exchange (BSE)",
            city="Mumbai",
            country="India",
            headquarters_address="Phiroze Jeejeebhoy Towers, Dalal Street, Fort, Mumbai, Maharashtra 400001, India",
            indices=[
                StockIndex(symbol="^BSESN", name="BSE Sensex"),
            ],
        ),
    ],
    "united states": [
        StockExchange(
            name="New York Stock Exchange (NYSE)",
            city="New York",
            country="United States",
            headquarters_address="11 Wall St, New York, NY 10005, USA",
            indices=[
                StockIndex(symbol="^GSPC", name="S&P 500"),
                StockIndex(symbol="^DJI", name="Dow Jones Industrial Average"),
            ],
        ),
        StockExchange(
            name="NASDAQ Stock Market",
            city="New York",
            country="United States",
            headquarters_address="151 W 42nd St, New York, NY 10036, USA",
            indices=[
                StockIndex(symbol="^IXIC", name="NASDAQ Composite"),
            ],
        ),
    ],
    "usa": [],  # will normalize to "united states"
    "united states of america": [],
    "japan": [
        StockExchange(
            name="Tokyo Stock Exchange (TSE)",
            city="Tokyo",
            country="Japan",
            headquarters_address="2-1 Nihonbashi Kabutocho, Chuo City, Tokyo 103-8224, Japan",
            indices=[
                StockIndex(symbol="^N225", name="Nikkei 225"),
                StockIndex(symbol="^TOPX", name="TOPIX"),
            ],
        ),
    ],
    "united kingdom": [
        StockExchange(
            name="London Stock Exchange (LSE)",
            city="London",
            country="United Kingdom",
            headquarters_address="10 Paternoster Square, London EC4M 7LS, United Kingdom",
            indices=[
                StockIndex(symbol="^FTSE", name="FTSE 100"),
                StockIndex(symbol="^FTMC", name="FTSE 250"),
            ],
        ),
    ],
    "uk": [],
    "south korea": [
        StockExchange(
            name="Korea Exchange (KRX) - Stock Market Division",
            city="Seoul",
            country="South Korea",
            headquarters_address="76 Yeouinaru-ro, Yeongdeungpo-gu, Seoul, South Korea",
            indices=[
                StockIndex(symbol="^KS11", name="KOSPI"),
                StockIndex(symbol="^KQ11", name="KOSDAQ"),
            ],
        ),
    ],
    "china": [
        StockExchange(
            name="Shanghai Stock Exchange (SSE)",
            city="Shanghai",
            country="China",
            headquarters_address="528 Pudong South Road, Pudong, Shanghai, China",
            indices=[
                StockIndex(symbol="000001.SS", name="SSE Composite Index"),
            ],
        ),
        StockExchange(
            name="Shenzhen Stock Exchange (SZSE)",
            city="Shenzhen",
            country="China",
            headquarters_address="2012 Shennan Blvd, Futian District, Shenzhen, Guangdong, China",
            indices=[
                StockIndex(symbol="399001.SZ", name="SZSE Component Index"),
            ],
        ),
    ],
}


def _normalize_country(country: str) -> str:
    return country.strip().lower()


def _resolve_profile_key(country: str) -> str:
    norm = _normalize_country(country)
    if norm in COUNTRY_STOCK_PROFILE and COUNTRY_STOCK_PROFILE[norm]:
        return norm
    # Map common aliases to canonical keys
    if norm in ("usa", "united states of america"):
        return "united states"
    if norm in ("uk", "great britain", "england"):
        return "united kingdom"
    return norm


def _fetch_latest_price(symbol: str) -> float | None:
    """
    Fetch the latest (most recent close) price for an index symbol from Yahoo Finance.
    """
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        if hist is None or hist.empty:
            return None
        # Take the most recent close value
        return float(hist["Close"].iloc[-1])
    except Exception:  # pragma: no cover - defensive
        return None


def get_country_stock_profile(country: str) -> Dict[str, Any]:
    """
    Return major stock exchanges, indices and latest index values for the given country.

    The response format:
    {
        "country": "...",
        "exchanges": [
            {
                "name": "...",
                "city": "...",
                "country": "...",
                "headquarters_address": "...",
                "indices": [
                    {
                        "symbol": "...",
                        "name": "...",
                        "last_price": 123.45 | null
                    },
                    ...
                ]
            },
            ...
        ],
        "error": "...",  # optional
    }
    """
    country_clean = country.strip()
    key = _resolve_profile_key(country)
    exchanges = COUNTRY_STOCK_PROFILE.get(key, [])

    if not exchanges:
        return {
            "country": country_clean,
            "exchanges": [],
            "error": "No stock exchange profile configured for this country.",
        }

    result_exchanges: List[Dict[str, Any]] = []
    for ex in exchanges:
        indices_with_prices: List[Dict[str, Any]] = []
        for idx in ex.indices:
            price = _fetch_latest_price(idx.symbol)
            indices_with_prices.append(
                {
                    "symbol": idx.symbol,
                    "name": idx.name,
                    "last_price": price,
                }
            )
        ex_dict = asdict(ex)
        ex_dict["indices"] = indices_with_prices
        result_exchanges.append(ex_dict)

    return {
        "country": country_clean,
        "exchanges": result_exchanges,
    }


__all__ = [
    "StockIndex",
    "StockExchange",
    "get_country_stock_profile",
]

