"""Utility functions for deckgl-marimo."""

from __future__ import annotations

import re


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


def to_snake_case(camel_str: str) -> str:
    """Convert camelCase to snake_case.

    Examples
    --------
    >>> to_snake_case("elevationScale")
    'elevation_scale'
    >>> to_snake_case("getFillColor")
    'get_fill_color'
    """
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", camel_str)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
