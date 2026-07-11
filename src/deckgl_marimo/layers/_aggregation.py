"""Aggregation deck.gl layer wrappers."""

from __future__ import annotations

from typing import Any

from deckgl_marimo._accessors import Accessor, PositionAccessor
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
    gpu_aggregation
        Whether to perform aggregation on the GPU. Default True.
    """

    LAYER_TYPE = "HexagonLayer"

    def __init__(
        self,
        *,
        data: Any = None,
        get_position: PositionAccessor | None = None,
        get_color_weight: Accessor = 1,
        get_color_value: Accessor | None = None,
        get_elevation_weight: Accessor = 1,
        get_elevation_value: Accessor | None = None,
        radius: int = 1000,
        elevation_scale: int = 1,
        elevation_range: tuple[float, float] = (0, 1000),
        color_domain: tuple[float, float] | None = None,
        elevation_domain: tuple[float, float] | None = None,
        color_range: list | None = None,
        color_aggregation: str = "SUM",
        elevation_aggregation: str = "SUM",
        color_scale_type: str = "quantize",
        elevation_scale_type: str = "linear",
        extruded: bool = False,
        coverage: float = 1.0,
        upper_percentile: int = 100,
        lower_percentile: int = 0,
        elevation_upper_percentile: int = 100,
        elevation_lower_percentile: int = 0,
        gpu_aggregation: bool = True,
        **kwargs: Any,
    ) -> None:
        props: dict[str, Any] = {
            "get_position": get_position,
            "get_color_weight": get_color_weight,
            "get_elevation_weight": get_elevation_weight,
            "radius": radius,
            "elevation_scale": elevation_scale,
            "elevation_range": list(elevation_range),
            "color_range": color_range or DEFAULT_COLOR_RANGE,
            "color_aggregation": color_aggregation,
            "elevation_aggregation": elevation_aggregation,
            "color_scale_type": color_scale_type,
            "elevation_scale_type": elevation_scale_type,
            "extruded": extruded,
            "coverage": coverage,
            "upper_percentile": upper_percentile,
            "lower_percentile": lower_percentile,
            "elevation_upper_percentile": elevation_upper_percentile,
            "elevation_lower_percentile": elevation_lower_percentile,
            "gpu_aggregation": gpu_aggregation,
        }
        if get_color_value is not None:
            props["get_color_value"] = get_color_value
        if get_elevation_value is not None:
            props["get_elevation_value"] = get_elevation_value
        if color_domain is not None:
            props["color_domain"] = list(color_domain)
        if elevation_domain is not None:
            props["elevation_domain"] = list(elevation_domain)
        super().__init__(data=data, **props, **kwargs)


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
        get_position: PositionAccessor | None = None,
        get_weight: Accessor = 1,
        radius_pixels: int = 30,
        intensity: float = 1,
        threshold: float = 0.05,
        color_range: list | None = None,
        color_domain: tuple[float, float] | None = None,
        aggregation: str = "SUM",
        debounce_timeout: int = 500,
        **kwargs: Any,
    ) -> None:
        props: dict[str, Any] = {
            "get_position": get_position,
            "get_weight": get_weight,
            "radius_pixels": radius_pixels,
            "intensity": intensity,
            "threshold": threshold,
            "color_range": color_range or DEFAULT_COLOR_RANGE,
            "aggregation": aggregation,
            "debounce_timeout": debounce_timeout,
        }
        if color_domain is not None:
            props["color_domain"] = list(color_domain)
        super().__init__(data=data, **props, **kwargs)


@_experimental
class ContourLayer(BaseLayer):
    """Render contour lines/bands from point data."""

    LAYER_TYPE = "ContourLayer"

    def __init__(
        self,
        *,
        data: Any = None,
        get_position: PositionAccessor | None = None,
        contours: list | None = None,
        cell_size: int = 1000,
        gpu_aggregation: bool = True,
        **kwargs: Any,
    ) -> None:
        props: dict[str, Any] = {"get_position": get_position, "cell_size": cell_size, "gpu_aggregation": gpu_aggregation}
        if contours is not None:
            props["contours"] = contours
        super().__init__(data=data, **props, **kwargs)


@_experimental
class GridLayer(BaseLayer):
    """Aggregate data into a rectangular grid."""

    LAYER_TYPE = "GridLayer"

    def __init__(
        self,
        *,
        data: Any = None,
        get_position: PositionAccessor | None = None,
        cell_size: int = 1000,
        color_range: list | None = None,
        extruded: bool = False,
        elevation_scale: float = 1,
        gpu_aggregation: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=data,
            get_position=get_position,
            cell_size=cell_size,
            color_range=color_range or DEFAULT_COLOR_RANGE,
            extruded=extruded,
            elevation_scale=elevation_scale,
            gpu_aggregation=gpu_aggregation,
            **kwargs,
        )


@_experimental
class ScreenGridLayer(BaseLayer):
    """Aggregate data into a screen-space grid."""

    LAYER_TYPE = "ScreenGridLayer"

    def __init__(
        self,
        *,
        data: Any = None,
        get_position: PositionAccessor | None = None,
        get_weight: Accessor = 1,
        cell_size_pixels: int = 100,
        color_range: list | None = None,
        gpu_aggregation: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=data,
            get_position=get_position,
            get_weight=get_weight,
            cell_size_pixels=cell_size_pixels,
            color_range=color_range or DEFAULT_COLOR_RANGE,
            gpu_aggregation=gpu_aggregation,
            **kwargs,
        )
