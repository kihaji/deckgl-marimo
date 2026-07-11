"""Typed MapLibre basemap composition for deckgl-marimo.

Compose a base style plus extra sources (WMS/XYZ raster, vector tiles,
GeoJSON) and MapLibre style layers from Python — no hand-written style
JSON. Pass a :class:`MapLibreConfig` as ``Map(basemap=...)``.
"""

from deckgl_marimo.maplibre._config import MapLibreConfig, empty_style
from deckgl_marimo.maplibre._layers import (
    BaseMapLibreLayer,
    CircleLayer,
    FillExtrusionLayer,
    FillLayer,
    LineLayer,
    RasterLayer,
    SymbolLayer,
)
from deckgl_marimo.maplibre._sources import GeoJSONSource, RasterSource, VectorSource

__all__ = [
    "MapLibreConfig",
    "empty_style",
    # Sources
    "RasterSource",
    "VectorSource",
    "GeoJSONSource",
    # Layers
    "BaseMapLibreLayer",
    "FillLayer",
    "LineLayer",
    "RasterLayer",
    "CircleLayer",
    "SymbolLayer",
    "FillExtrusionLayer",
]
