"""deckgl-marimo: deck.gl visualization library for marimo notebooks.

Provides deck.gl layers on MapLibre GL basemaps as interactive
anywidget-based widgets with full marimo reactivity support.
"""

from deckgl_marimo._accessors import Accessor, ColorAccessor, PositionAccessor
from deckgl_marimo._basemaps import Basemaps
from deckgl_marimo._color_scale import ColorScale
from deckgl_marimo._map import Map
from deckgl_marimo._view_state import ViewState

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

# Backward compatibility
from deckgl_marimo.widget import DeckGLHexagonWidget

__all__ = [
    # Widget
    "Map",
    "ViewState",
    "Basemaps",
    "ColorScale",
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
    # Backward compat
    "DeckGLHexagonWidget",
]
