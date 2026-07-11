"""Utility functions for deckgl-marimo."""

from __future__ import annotations



def to_camel_case(snake_str: str) -> str:
    """Convert snake_case to camelCase.

    Examples
    --------
    >>> to_camel_case("elevation_scale")
    'elevationScale'
    >>> to_camel_case("get_fill_color")
    'getFillColor'
    >>> to_camel_case("radius")
    'radius'
    """
    parts = snake_str.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])
