"""Aggregation deck.gl layer wrappers."""

from __future__ import annotations

import warnings
from typing import Any

from deckgl_marimo._base import BaseLayer
from deckgl_marimo.layers._core import _experimental

DEFAULT_COLOR_RANGE = [
    [1, 152, 189],
    [73, 227, 206],
    [216, 254, 181],
    [254, 237, 177],
    [254, 173, 84],
    [209, 55, 78],
]


class HexagonLayer(BaseLayer):
    """Aggregate data into hexagonal bins.

    Parameters
    ----------
    data
        Input data with position coordinates.
    get_position
        Position accessor, e.g. ``["lon", "lat"]``.
    radius
        Hexagon bin radius in meters.
    elevation_scale
        Height multiplier for extruded hexagons.
    color_range
        6-step color ramp as list of ``[r, g, b]`` lists.
    extruded
        Whether to render hexagons as 3D columns.
    coverage
        Hexagon coverage ratio (0-1).
    upper_percentile
        Upper data percentile for color mapping (0-100).
    """

    LAYER_TYPE = "HexagonLayer"

    def __init__(
        self,
        *,
        data: Any = None,
        get_position: Any = None,
        radius: int = 1000,
        elevation_scale: int = 1,
        color_range: list | None = None,
        extruded: bool = False,
        coverage: float = 1.0,
        upper_percentile: int = 100,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=data,
            get_position=get_position,
            radius=radius,
            elevation_scale=elevation_scale,
            color_range=color_range or DEFAULT_COLOR_RANGE,
            extruded=extruded,
            coverage=coverage,
            upper_percentile=upper_percentile,
            **kwargs,
        )


class HeatmapLayer(BaseLayer):
    """Render a density heatmap.

    Parameters
    ----------
    data
        Input data with position coordinates.
    get_position
        Position accessor.
    get_weight
        Weight accessor. Column name or constant.
    radius_pixels
        Heatmap kernel radius in pixels.
    intensity
        Heatmap intensity multiplier.
    threshold
        Minimum value threshold (0-1).
    color_range
        Color ramp for the heatmap.
    """

    LAYER_TYPE = "HeatmapLayer"

    def __init__(
        self,
        *,
        data: Any = None,
        get_position: Any = None,
        get_weight: Any = 1,
        radius_pixels: int = 30,
        intensity: float = 1,
        threshold: float = 0.05,
        color_range: list | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=data,
            get_position=get_position,
            get_weight=get_weight,
            radius_pixels=radius_pixels,
            intensity=intensity,
            threshold=threshold,
            color_range=color_range or DEFAULT_COLOR_RANGE,
            **kwargs,
        )


@_experimental
class ContourLayer(BaseLayer):
    """Render contour lines/bands from point data."""

    LAYER_TYPE = "ContourLayer"

    def __init__(self, *, data: Any = None, get_position: Any = None, contours: list | None = None, cell_size: int = 1000, **kwargs: Any) -> None:
        props: dict[str, Any] = {"get_position": get_position, "cell_size": cell_size}
        if contours is not None:
            props["contours"] = contours
        super().__init__(data=data, **props, **kwargs)


@_experimental
class GridLayer(BaseLayer):
    """Aggregate data into a rectangular grid."""

    LAYER_TYPE = "GridLayer"

    def __init__(self, *, data: Any = None, get_position: Any = None, cell_size: int = 1000, color_range: list | None = None, extruded: bool = False, elevation_scale: float = 1, **kwargs: Any) -> None:
        super().__init__(
            data=data,
            get_position=get_position,
            cell_size=cell_size,
            color_range=color_range or DEFAULT_COLOR_RANGE,
            extruded=extruded,
            elevation_scale=elevation_scale,
            **kwargs,
        )


@_experimental
class ScreenGridLayer(BaseLayer):
    """Aggregate data into a screen-space grid."""

    LAYER_TYPE = "ScreenGridLayer"

    def __init__(self, *, data: Any = None, get_position: Any = None, get_weight: Any = 1, cell_size_pixels: int = 100, color_range: list | None = None, **kwargs: Any) -> None:
        super().__init__(
            data=data,
            get_position=get_position,
            get_weight=get_weight,
            cell_size_pixels=cell_size_pixels,
            color_range=color_range or DEFAULT_COLOR_RANGE,
            **kwargs,
        )
