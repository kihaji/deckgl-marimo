"""Geo deck.gl layer wrappers."""

from __future__ import annotations

from typing import Any

from deckgl_marimo._accessors import Accessor, ColorAccessor, PositionAccessor
from deckgl_marimo._base import BaseLayer
from deckgl_marimo.layers._core import _experimental


@_experimental
class GreatCircleLayer(BaseLayer):
    """Render great circle arcs between points."""

    LAYER_TYPE = "GreatCircleLayer"

    def __init__(
        self,
        *,
        data: Any = None,
        get_source_position: PositionAccessor | None = None,
        get_target_position: PositionAccessor | None = None,
        get_source_color: ColorAccessor = (0, 0, 255, 255),
        get_target_color: ColorAccessor = (0, 200, 0, 255),
        get_width: Accessor = 1,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=data,
            get_source_position=get_source_position,
            get_target_position=get_target_position,
            get_source_color=list(get_source_color) if isinstance(get_source_color, tuple) else get_source_color,
            get_target_color=list(get_target_color) if isinstance(get_target_color, tuple) else get_target_color,
            get_width=get_width,
            **kwargs,
        )


@_experimental
class H3ClusterLayer(BaseLayer):
    """Render clustered H3 hexagons."""

    LAYER_TYPE = "H3ClusterLayer"

    def __init__(
        self,
        *,
        data: Any = None,
        get_hexagons: PositionAccessor | None = None,
        get_fill_color: ColorAccessor = (0, 0, 0, 255),
        get_line_color: ColorAccessor = (0, 0, 0, 255),
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=data,
            get_hexagons=get_hexagons,
            get_fill_color=list(get_fill_color) if isinstance(get_fill_color, tuple) else get_fill_color,
            get_line_color=list(get_line_color) if isinstance(get_line_color, tuple) else get_line_color,
            **kwargs,
        )


@_experimental
class H3HexagonLayer(BaseLayer):
    """Render individual H3 hexagons."""

    LAYER_TYPE = "H3HexagonLayer"

    def __init__(
        self,
        *,
        data: Any = None,
        get_hexagon: PositionAccessor | None = None,
        get_fill_color: ColorAccessor = (0, 0, 0, 255),
        get_elevation: Accessor = 1000,
        extruded: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=data,
            get_hexagon=get_hexagon,
            get_fill_color=list(get_fill_color) if isinstance(get_fill_color, tuple) else get_fill_color,
            get_elevation=get_elevation,
            extruded=extruded,
            **kwargs,
        )


@_experimental
class MVTLayer(BaseLayer):
    """Render Mapbox Vector Tiles."""

    LAYER_TYPE = "MVTLayer"

    def __init__(
        self,
        *,
        data: Any = None,
        get_fill_color: ColorAccessor = (0, 0, 0, 255),
        get_line_color: ColorAccessor = (0, 0, 0, 255),
        get_line_width: Accessor = 1,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=data,
            get_fill_color=list(get_fill_color) if isinstance(get_fill_color, tuple) else get_fill_color,
            get_line_color=list(get_line_color) if isinstance(get_line_color, tuple) else get_line_color,
            get_line_width=get_line_width,
            **kwargs,
        )


@_experimental
class QuadkeyLayer(BaseLayer):
    """Render data indexed by Quadkey."""

    LAYER_TYPE = "QuadkeyLayer"

    def __init__(
        self,
        *,
        data: Any = None,
        get_quadkey: PositionAccessor | None = None,
        get_fill_color: ColorAccessor = (0, 0, 0, 255),
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=data,
            get_quadkey=get_quadkey,
            get_fill_color=list(get_fill_color) if isinstance(get_fill_color, tuple) else get_fill_color,
            **kwargs,
        )


@_experimental
class S2Layer(BaseLayer):
    """Render data indexed by S2 cell tokens."""

    LAYER_TYPE = "S2Layer"

    def __init__(
        self,
        *,
        data: Any = None,
        get_s2_token: PositionAccessor | None = None,
        get_fill_color: ColorAccessor = (0, 0, 0, 255),
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=data,
            get_s2_token=get_s2_token,
            get_fill_color=list(get_fill_color) if isinstance(get_fill_color, tuple) else get_fill_color,
            **kwargs,
        )


@_experimental
class TerrainLayer(BaseLayer):
    """Render 3D terrain meshes from elevation data."""

    LAYER_TYPE = "TerrainLayer"

    def __init__(
        self,
        *,
        data: Any = None,
        elevation_data: str | None = None,
        texture: str | None = None,
        elevation_decoder: dict | None = None,
        **kwargs: Any,
    ) -> None:
        props: dict[str, Any] = {}
        if elevation_data is not None:
            props["elevation_data"] = elevation_data
        if texture is not None:
            props["texture"] = texture
        if elevation_decoder is not None:
            props["elevation_decoder"] = elevation_decoder
        super().__init__(data=data, **props, **kwargs)


@_experimental
class TileLayer(BaseLayer):
    """Render map tiles from a tile server."""

    LAYER_TYPE = "TileLayer"

    def __init__(self, *, data: Any = None, min_zoom: int = 0, max_zoom: int = 19, tile_size: int = 256, **kwargs: Any) -> None:
        super().__init__(data=data, min_zoom=min_zoom, max_zoom=max_zoom, tile_size=tile_size, **kwargs)


@_experimental
class Tile3DLayer(BaseLayer):
    """Render 3D tiles (e.g., from Cesium ion)."""

    LAYER_TYPE = "Tile3DLayer"

    def __init__(self, *, data: Any = None, **kwargs: Any) -> None:
        super().__init__(data=data, **kwargs)


@_experimental
class TripsLayer(BaseLayer):
    """Render animated trip paths."""

    LAYER_TYPE = "TripsLayer"

    def __init__(
        self,
        *,
        data: Any = None,
        get_path: PositionAccessor | None = None,
        get_timestamps: Accessor | None = None,
        get_color: ColorAccessor = (0, 0, 0, 255),
        current_time: float = 0,
        trail_length: float = 120,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=data,
            get_path=get_path,
            get_timestamps=get_timestamps,
            get_color=list(get_color) if isinstance(get_color, tuple) else get_color,
            current_time=current_time,
            trail_length=trail_length,
            **kwargs,
        )
