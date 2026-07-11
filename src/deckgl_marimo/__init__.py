"""deckgl-marimo: deck.gl visualization library for marimo notebooks.

Provides deck.gl layers on MapLibre GL basemaps as interactive
anywidget-based widgets with full marimo reactivity support.
"""

from deckgl_marimo._accessors import Accessor, ColorAccessor, PositionAccessor
from deckgl_marimo._basemaps import Basemaps
from deckgl_marimo._binary import pack_binary, pack_polygon_binary
from deckgl_marimo._bounds import compute_bounds
from deckgl_marimo._color_scale import ColorScale
from deckgl_marimo._map import Map

# Core layers (fully tested)
from deckgl_marimo.layers._core import (
    ArcLayer,
    ColumnLayer,
    GeoJsonLayer,
    IconLayer,
    LineLayer,
    PathLayer,
    PointCloudLayer,
    PolygonLayer,
    ScatterplotLayer,
    SolidPolygonLayer,
    TextLayer,
)

# Aggregation layers (fully tested)
from deckgl_marimo.layers._aggregation import (
    HeatmapLayer,
    HexagonLayer,
)

# Composite layers
from deckgl_marimo.layers._composite import (
    DisplacementLayer,
    EllipseLayer,
)

__all__ = [
    # Widget
    "Map",
    "Basemaps",
    "ColorScale",
    # Binary packing
    "pack_binary",
    "pack_polygon_binary",
    # Bounds
    "compute_bounds",
    # Accessor type aliases
    "Accessor",
    "ColorAccessor",
    "PositionAccessor",
    # Core layers
    "ArcLayer",
    "ColumnLayer",
    "GeoJsonLayer",
    "IconLayer",
    "LineLayer",
    "PathLayer",
    "PointCloudLayer",
    "PolygonLayer",
    "ScatterplotLayer",
    "SolidPolygonLayer",
    "TextLayer",
    # Aggregation layers
    "HeatmapLayer",
    "HexagonLayer",
    # Composite layers
    "DisplacementLayer",
    "EllipseLayer",
]
