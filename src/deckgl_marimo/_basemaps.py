"""Basemap catalog for deckgl-marimo."""

from __future__ import annotations


class Basemaps:
    """Catalog of free basemap styles for MapLibre GL.

    Use class attributes for direct access, or use :meth:`resolve`
    to look up by alias.

    Examples
    --------
    >>> Basemaps.resolve("dark-matter")
    'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json'
    >>> Basemaps.resolve("https://my-tiles.example.com/style.json")
    'https://my-tiles.example.com/style.json'
    """

    # CARTO free basemaps
    CARTO_DARK = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
    CARTO_LIGHT = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
    CARTO_VOYAGER = "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json"

    # OpenFreeMap
    OSM_LIBERTY = "https://tiles.openfreemap.org/styles/liberty"
    OSM_BRIGHT = "https://tiles.openfreemap.org/styles/bright"
    OSM_POSITRON = "https://tiles.openfreemap.org/styles/positron"

    _ALIASES: dict[str, str] = {
        "dark-matter": CARTO_DARK,
        "dark": CARTO_DARK,
        "light": CARTO_LIGHT,
        "positron": CARTO_LIGHT,
        "voyager": CARTO_VOYAGER,
        "liberty": OSM_LIBERTY,
        "bright": OSM_BRIGHT,
        "osm": OSM_LIBERTY,
        "none": "",
    }

    @classmethod
    def resolve(cls, name_or_url: str) -> str:
        """Resolve a basemap alias to a style URL.

        If the input matches a known alias, returns the corresponding URL.
        Otherwise, returns the input as-is (assumed to be a direct URL).
        """
        return cls._ALIASES.get(name_or_url, name_or_url)

    @classmethod
    def list_available(cls) -> list[str]:
        """Return a list of available basemap alias names."""
        return sorted(cls._ALIASES.keys())
