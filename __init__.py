"""
Tool factory functions for the Country Financial Insights agent.

These helpers expose LangChain-compatible tools that are thin wrappers
around the concrete implementations in the sibling modules.
"""

from .currency_tool import (
    get_currency_for_country,
    get_exchange_rates_for_currency,
)
from .stock_tool import get_country_stock_profile
from .maps_tool import get_google_maps_link_for_address

from langchain_core.tools import tool


@tool("get_currency_for_country")
def get_currency_for_country_tool(country: str) -> dict:
    """Return the official currency name and ISO code for a given country.

    Args:
        country: Country name, e.g. "India" or "United States".
    """
    return get_currency_for_country(country)


@tool("get_exchange_rates_for_currency")
def get_exchange_rates_for_currency_tool(currency_code: str) -> dict:
    """Return exchange rates for 1 unit of the given currency against USD, INR, GBP, and EUR.

    Args:
        currency_code: ISO 4217 currency code, e.g. "INR" or "USD".
    """
    return get_exchange_rates_for_currency(currency_code)


@tool("get_country_stock_profile")
def get_country_stock_profile_tool(country: str) -> dict:
    """Return major stock exchanges, indices, and latest index values for the given country."""
    return get_country_stock_profile(country)


@tool("get_google_maps_link_for_address")
def get_google_maps_link_for_address_tool(address: str) -> str:
    """Return a Google Maps URL for the given postal address or landmark name."""
    return get_google_maps_link_for_address(address)


__all__ = [
    "get_currency_for_country",
    "get_exchange_rates_for_currency",
    "get_country_stock_profile",
    "get_google_maps_link_for_address",
    # LangChain tools
    "get_currency_for_country_tool",
    "get_exchange_rates_for_currency_tool",
    "get_country_stock_profile_tool",
    "get_google_maps_link_for_address_tool",
]

