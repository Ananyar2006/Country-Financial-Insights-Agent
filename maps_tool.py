"""
Maps tools: generate Google Maps links for stock exchange headquarters.

We do not need a Google Maps API key for simple clickable links; we just
construct a search URL for the provided address.
"""

from __future__ import annotations

import urllib.parse


def get_google_maps_link_for_address(address: str) -> str:
    """
    Build a Google Maps search URL for the given address or landmark.

    Example:
        >>> get_google_maps_link_for_address("11 Wall St, New York, NY 10005, USA")
        'https://www.google.com/maps/search/?api=1&query=11%20Wall%20St%2C%20New%20York%2C%20NY%2010005%2C%20USA'
    """
    query = urllib.parse.quote_plus(address.strip())
    return f"https://www.google.com/maps/search/?api=1&query={query}"


__all__ = [
    "get_google_maps_link_for_address",
]

