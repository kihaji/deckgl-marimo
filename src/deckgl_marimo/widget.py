"""DeckGLHexagonWidget — anywidget wrapping MapLibre GL JS + deck.gl HexagonLayer."""

from __future__ import annotations

import pathlib
from typing import Any

import anywidget
import traitlets

from deckgl_marimo._data import dataframe_to_positions

DEFAULT_COLOR_RANGE = [
    [1, 152, 189],
    [73, 227, 206],
    [216, 254, 181],
    [254, 237, 177],
    [254, 173, 84],
    [209, 55, 78],
]

_HERE = pathlib.Path(__file__).parent


class DeckGLHexagonWidget(anywidget.AnyWidget):
    """A deck.gl HexagonLayer rendered on a MapLibre GL JS base map.

    Parameters
    ----------
    style_url : str
        MapLibre style URL (required, no default).
    data : DataFrame or list[dict], optional
        Source data with lat/lon columns.
    lat_col, lon_col : str
        Column names for latitude and longitude.
    center_lon, center_lat : float
        Initial map center.
    zoom, pitch, bearing : float
        Initial view state.
    radius, elevation_scale : int
        HexagonLayer parameters.
    color_range : list
        6-step color ramp as list of [r, g, b] lists.
    extruded, pickable : bool
        HexagonLayer flags.
    coverage, upper_percentile : float
        HexagonLayer parameters.
    map_height : str
        CSS height of the map container.
    """

    _esm = _HERE / "widget.js"
    _css = _HERE / "widget.css"

    # Map style
    style_url = traitlets.Unicode().tag(sync=True)

    # Positions data — [[lon, lat], ...]
    positions = traitlets.List(traitlets.List()).tag(sync=True)

    # View state
    center_lon = traitlets.Float(-1.4157).tag(sync=True)
    center_lat = traitlets.Float(52.2324).tag(sync=True)
    zoom = traitlets.Float(6.0).tag(sync=True)
    pitch = traitlets.Float(40.5).tag(sync=True)
    bearing = traitlets.Float(0.0).tag(sync=True)

    # HexagonLayer params
    radius = traitlets.Int(1000).tag(sync=True)
    elevation_scale = traitlets.Int(250).tag(sync=True)
    color_range = traitlets.List(DEFAULT_COLOR_RANGE).tag(sync=True)
    extruded = traitlets.Bool(True).tag(sync=True)
    coverage = traitlets.Float(1.0).tag(sync=True)
    upper_percentile = traitlets.Int(100).tag(sync=True)
    pickable = traitlets.Bool(True).tag(sync=True)

    # Layout
    map_height = traitlets.Unicode("600px").tag(sync=True)

    # Viewport read-back from JS (read-only on Python side)
    viewport = traitlets.Dict({}).tag(sync=True)

    def __init__(
        self,
        style_url: str,
        data: Any = None,
        lat_col: str = "lat",
        lon_col: str = "lon",
        **kwargs: Any,
    ) -> None:
        positions = []
        if data is not None:
            positions = dataframe_to_positions(data, lat_col=lat_col, lon_col=lon_col)
        super().__init__(style_url=style_url, positions=positions, **kwargs)
