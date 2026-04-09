"""Core deck.gl layer wrappers."""

from __future__ import annotations

import warnings
from typing import Any

from deckgl_marimo._base import BaseLayer
from deckgl_marimo._binary import BinaryAttr, BinaryConfig


def _experimental(cls: type) -> type:
    """Mark a layer class as experimental."""
    original_init = cls.__init__

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        warnings.warn(
            f"{cls.__name__} is experimental and may not be fully tested.",
            stacklevel=2,
        )
        original_init(self, *args, **kwargs)

    cls.__init__ = __init__
    cls._experimental = True
    return cls


class ScatterplotLayer(BaseLayer):
    """Render circles at given positions.

    Parameters
    ----------
    data
        Input data (DataFrame, list of dicts, etc.)
    get_position
        Accessor for position. Column name(s) like ``["lon", "lat"]``.
    get_fill_color
        Fill color accessor. Column name or constant like ``[255, 0, 0]``.
    get_line_color
        Outline color accessor.
    get_radius
        Radius accessor. Column name or constant in meters.
    radius_scale
        Global radius multiplier.
    radius_min_pixels
        Minimum circle radius in pixels.
    radius_max_pixels
        Maximum circle radius in pixels.
    line_width_min_pixels
        Minimum outline width in pixels.
    stroked
        Whether to draw outlines.
    filled
        Whether to fill circles.
    billboard
        Whether circles always face the camera.
    """

    LAYER_TYPE = "ScatterplotLayer"
    BINARY = BinaryConfig(attrs=(
        BinaryAttr("get_position", "float32", 2, fast_key="positions"),
        BinaryAttr("get_fill_color", "uint8", 4, fast_key="colors"),
        BinaryAttr("get_radius", "float32", 1, fast_key="radii"),
    ))

    def __init__(
        self,
        *,
        data: Any = None,
        get_position: Any = None,
        get_fill_color: Any = (0, 0, 0, 255),
        get_line_color: Any = (0, 0, 0, 255),
        get_radius: Any = 1,
        radius_scale: float = 1,
        radius_min_pixels: float = 0,
        radius_max_pixels: float = float("inf"),
        line_width_min_pixels: float = 0,
        stroked: bool = False,
        filled: bool = True,
        billboard: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=data,
            get_position=get_position,
            get_fill_color=list(get_fill_color) if isinstance(get_fill_color, tuple) else get_fill_color,
            get_line_color=list(get_line_color) if isinstance(get_line_color, tuple) else get_line_color,
            get_radius=get_radius,
            radius_scale=radius_scale,
            radius_min_pixels=radius_min_pixels,
            radius_max_pixels=radius_max_pixels,
            line_width_min_pixels=line_width_min_pixels,
            stroked=stroked,
            filled=filled,
            billboard=billboard,
            **kwargs,
        )


class GeoJsonLayer(BaseLayer):
    """Render GeoJSON data (points, lines, polygons).

    For authenticated remote data, use ``fetch_headers`` or
    ``load_options``::

        GeoJsonLayer(
            data="https://secure-api.example.com/data.geojson",
            fetch_headers={"Authorization": "Bearer my-token"},
        )

    Parameters
    ----------
    data
        GeoJSON dict, GeoDataFrame, URL, or file path.
    get_fill_color
        Fill color for polygons/points.
    get_line_color
        Stroke color for lines/polygon outlines.
    get_line_width
        Line width accessor.
    get_point_radius
        Radius for point features.
    filled
        Whether to fill polygons.
    stroked
        Whether to stroke polygon outlines.
    extruded
        Whether to extrude polygons in 3D.
    point_type
        How to render points: ``"circle"``, ``"icon"``, ``"text"``, or
        ``"circle+text"``.
    line_width_min_pixels
        Minimum line width in pixels.
    """

    LAYER_TYPE = "GeoJsonLayer"

    def __init__(
        self,
        *,
        data: Any = None,
        get_fill_color: Any = (0, 0, 0, 255),
        get_line_color: Any = (0, 0, 0, 255),
        get_line_width: Any = 1,
        get_point_radius: Any = 1,
        filled: bool = True,
        stroked: bool = True,
        extruded: bool = False,
        point_type: str = "circle",
        line_width_min_pixels: float = 0,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=data,
            get_fill_color=list(get_fill_color) if isinstance(get_fill_color, tuple) else get_fill_color,
            get_line_color=list(get_line_color) if isinstance(get_line_color, tuple) else get_line_color,
            get_line_width=get_line_width,
            get_point_radius=get_point_radius,
            filled=filled,
            stroked=stroked,
            extruded=extruded,
            point_type=point_type,
            line_width_min_pixels=line_width_min_pixels,
            **kwargs,
        )


class ArcLayer(BaseLayer):
    """Render arcs between source and target positions.

    Parameters
    ----------
    data
        Input data with source/target coordinates.
    get_source_position
        Source position accessor, e.g. ``["src_lon", "src_lat"]``.
    get_target_position
        Target position accessor, e.g. ``["dst_lon", "dst_lat"]``.
    get_source_color
        Source arc color.
    get_target_color
        Target arc color.
    get_width
        Arc width accessor.
    great_circle
        Whether to draw great circle arcs.
    """

    LAYER_TYPE = "ArcLayer"
    BINARY = BinaryConfig(attrs=(
        BinaryAttr("get_source_position", "float32", 2, fast_key="source_positions"),
        BinaryAttr("get_target_position", "float32", 2, fast_key="target_positions"),
        BinaryAttr("get_source_color", "uint8", 4, fast_key="source_colors"),
        BinaryAttr("get_target_color", "uint8", 4, fast_key="target_colors"),
    ))

    def __init__(
        self,
        *,
        data: Any = None,
        get_source_position: Any = None,
        get_target_position: Any = None,
        get_source_color: Any = (0, 0, 255, 255),
        get_target_color: Any = (0, 200, 0, 255),
        get_width: Any = 1,
        great_circle: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=data,
            get_source_position=get_source_position,
            get_target_position=get_target_position,
            get_source_color=list(get_source_color) if isinstance(get_source_color, tuple) else get_source_color,
            get_target_color=list(get_target_color) if isinstance(get_target_color, tuple) else get_target_color,
            get_width=get_width,
            great_circle=great_circle,
            **kwargs,
        )


class PathLayer(BaseLayer):
    """Render polyline paths.

    Parameters
    ----------
    data
        Input data containing path coordinates.
    get_path
        Path accessor. Column name containing coordinate arrays.
    get_color
        Path color accessor.
    get_width
        Path width accessor.
    width_scale
        Global width multiplier.
    width_min_pixels
        Minimum width in pixels.
    rounded
        Whether to use rounded joints and caps.
    billboard
        Whether paths always face the camera.
    """

    LAYER_TYPE = "PathLayer"
    BINARY = BinaryConfig(attrs=(
        BinaryAttr("get_path", "float32", 2, fast_key="path_coords", is_geometry=True),
        BinaryAttr("get_color", "uint8", 4, fast_key="colors", per_vertex=True),
    ))

    def __init__(
        self,
        *,
        data: Any = None,
        get_path: Any = None,
        get_color: Any = (0, 0, 0, 255),
        get_width: Any = 1,
        width_scale: float = 1,
        width_min_pixels: float = 0,
        rounded: bool = False,
        billboard: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=data,
            get_path=get_path,
            get_color=list(get_color) if isinstance(get_color, tuple) else get_color,
            get_width=get_width,
            width_scale=width_scale,
            width_min_pixels=width_min_pixels,
            rounded=rounded,
            billboard=billboard,
            **kwargs,
        )


class PolygonLayer(BaseLayer):
    """Render filled and/or stroked polygons.

    Parameters
    ----------
    data
        Input data containing polygon coordinates.
    get_polygon
        Polygon accessor. Column name containing coordinate arrays.
    get_fill_color
        Fill color accessor.
    get_line_color
        Outline color accessor.
    get_line_width
        Outline width accessor.
    filled
        Whether to fill polygons.
    stroked
        Whether to draw outlines.
    extruded
        Whether to extrude in 3D.
    get_elevation
        Elevation accessor for 3D extrusion.
    elevation_scale
        Global elevation multiplier.
    """

    LAYER_TYPE = "PolygonLayer"
    BINARY = BinaryConfig(
        attrs=(
            BinaryAttr("get_polygon", "float32", 2, fast_key="polygon_coords", is_geometry=True),
            BinaryAttr("get_fill_color", "uint8", 4, fast_key="colors", per_vertex=True),
        ),
        binary_type_override="SolidPolygonLayer",
    )

    def __init__(
        self,
        *,
        data: Any = None,
        get_polygon: Any = None,
        get_fill_color: Any = (0, 0, 0, 255),
        get_line_color: Any = (0, 0, 0, 255),
        get_line_width: Any = 1,
        filled: bool = True,
        stroked: bool = True,
        extruded: bool = False,
        get_elevation: Any = 1000,
        elevation_scale: float = 1,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=data,
            get_polygon=get_polygon,
            get_fill_color=list(get_fill_color) if isinstance(get_fill_color, tuple) else get_fill_color,
            get_line_color=list(get_line_color) if isinstance(get_line_color, tuple) else get_line_color,
            get_line_width=get_line_width,
            filled=filled,
            stroked=stroked,
            extruded=extruded,
            get_elevation=get_elevation,
            elevation_scale=elevation_scale,
            **kwargs,
        )


class IconLayer(BaseLayer):
    """Render icons at given positions.

    Parameters
    ----------
    data
        Input data with position and icon info.
    get_position
        Position accessor.
    get_icon
        Icon accessor. Returns icon name or object.
    get_size
        Icon size accessor.
    get_color
        Icon tint color accessor.
    get_angle
        Icon rotation angle accessor.
    icon_atlas
        URL or image of the icon atlas spritesheet.
    icon_mapping
        Dict mapping icon names to atlas regions.
    size_scale
        Global size multiplier.
    billboard
        Whether icons always face the camera.
    """

    LAYER_TYPE = "IconLayer"

    def __init__(
        self,
        *,
        data: Any = None,
        get_position: Any = None,
        get_icon: Any = None,
        get_size: Any = 1,
        get_color: Any = (0, 0, 0, 255),
        get_angle: Any = 0,
        icon_atlas: str | None = None,
        icon_mapping: dict | None = None,
        size_scale: float = 1,
        billboard: bool = True,
        **kwargs: Any,
    ) -> None:
        props: dict[str, Any] = {
            "get_position": get_position,
            "get_icon": get_icon,
            "get_size": get_size,
            "get_color": list(get_color) if isinstance(get_color, tuple) else get_color,
            "get_angle": get_angle,
            "size_scale": size_scale,
            "billboard": billboard,
        }
        if icon_atlas is not None:
            props["icon_atlas"] = icon_atlas
        if icon_mapping is not None:
            props["icon_mapping"] = icon_mapping
        super().__init__(data=data, **props, **kwargs)


class TextLayer(BaseLayer):
    """Render text labels at given positions.

    Parameters
    ----------
    data
        Input data with position and text info.
    get_position
        Position accessor.
    get_text
        Text content accessor. Column name containing strings.
    get_size
        Font size accessor.
    get_color
        Text color accessor.
    get_angle
        Text rotation angle accessor.
    get_alignment_baseline
        Vertical alignment: ``"top"``, ``"center"``, ``"bottom"``.
    get_text_anchor
        Horizontal alignment: ``"start"``, ``"middle"``, ``"end"``.
    font_family
        CSS font family.
    size_scale
        Global size multiplier.
    billboard
        Whether text always faces the camera.
    """

    LAYER_TYPE = "TextLayer"

    def __init__(
        self,
        *,
        data: Any = None,
        get_position: Any = None,
        get_text: Any = None,
        get_size: Any = 32,
        get_color: Any = (0, 0, 0, 255),
        get_angle: Any = 0,
        get_alignment_baseline: str = "center",
        get_text_anchor: str = "middle",
        font_family: str = "Monaco, monospace",
        size_scale: float = 1,
        billboard: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=data,
            get_position=get_position,
            get_text=get_text,
            get_size=get_size,
            get_color=list(get_color) if isinstance(get_color, tuple) else get_color,
            get_angle=get_angle,
            get_alignment_baseline=get_alignment_baseline,
            get_text_anchor=get_text_anchor,
            font_family=font_family,
            size_scale=size_scale,
            billboard=billboard,
            **kwargs,
        )


class ColumnLayer(BaseLayer):
    """Render 3D columns (cylinders/prisms) at given positions.

    Parameters
    ----------
    data
        Input data with position info.
    get_position
        Position accessor.
    get_fill_color
        Column fill color accessor.
    get_line_color
        Column outline color accessor.
    get_elevation
        Column height accessor.
    disk_resolution
        Number of sides for the column polygon (higher = more circular).
    radius
        Column radius in meters.
    elevation_scale
        Global elevation multiplier.
    extruded
        Whether to extrude (must be True for 3D).
    """

    LAYER_TYPE = "ColumnLayer"
    BINARY = BinaryConfig(attrs=(
        BinaryAttr("get_position", "float32", 2, fast_key="positions"),
        BinaryAttr("get_fill_color", "uint8", 4, fast_key="colors"),
        BinaryAttr("get_elevation", "float32", 1, fast_key="elevations"),
    ))

    def __init__(
        self,
        *,
        data: Any = None,
        get_position: Any = None,
        get_fill_color: Any = (255, 0, 0, 255),
        get_line_color: Any = (0, 0, 0, 255),
        get_elevation: Any = 1000,
        disk_resolution: int = 20,
        radius: float = 1000,
        elevation_scale: float = 1,
        extruded: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=data,
            get_position=get_position,
            get_fill_color=list(get_fill_color) if isinstance(get_fill_color, tuple) else get_fill_color,
            get_line_color=list(get_line_color) if isinstance(get_line_color, tuple) else get_line_color,
            get_elevation=get_elevation,
            disk_resolution=disk_resolution,
            radius=radius,
            elevation_scale=elevation_scale,
            extruded=extruded,
            **kwargs,
        )


# --- Experimental Core Layers ---


@_experimental
class BitmapLayer(BaseLayer):
    """Render a bitmap image on the map."""

    LAYER_TYPE = "BitmapLayer"

    def __init__(self, *, data: Any = None, image: str | None = None, bounds: Any = None, **kwargs: Any) -> None:
        props: dict[str, Any] = {}
        if image is not None:
            props["image"] = image
        if bounds is not None:
            props["bounds"] = bounds
        super().__init__(data=data, **props, **kwargs)


@_experimental
class GridCellLayer(BaseLayer):
    """Render grid cells (used internally by GridLayer)."""

    LAYER_TYPE = "GridCellLayer"

    def __init__(self, *, data: Any = None, **kwargs: Any) -> None:
        super().__init__(data=data, **kwargs)


@_experimental
class LineLayer(BaseLayer):
    """Render straight lines between pairs of points."""

    LAYER_TYPE = "LineLayer"
    BINARY = BinaryConfig(attrs=(
        BinaryAttr("get_source_position", "float32", 2, fast_key="source_positions"),
        BinaryAttr("get_target_position", "float32", 2, fast_key="target_positions"),
        BinaryAttr("get_color", "uint8", 4, fast_key="colors"),
    ))

    def __init__(
        self,
        *,
        data: Any = None,
        get_source_position: Any = None,
        get_target_position: Any = None,
        get_color: Any = (0, 0, 0, 255),
        get_width: Any = 1,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=data,
            get_source_position=get_source_position,
            get_target_position=get_target_position,
            get_color=list(get_color) if isinstance(get_color, tuple) else get_color,
            get_width=get_width,
            **kwargs,
        )


@_experimental
class PointCloudLayer(BaseLayer):
    """Render a point cloud."""

    LAYER_TYPE = "PointCloudLayer"
    BINARY = BinaryConfig(attrs=(
        BinaryAttr("get_position", "float32", 0, fast_key="positions"),  # size=0: infer 2D or 3D
        BinaryAttr("get_color", "uint8", 4, fast_key="colors"),
        BinaryAttr("get_normal", "float32", 3, fast_key="normals"),
    ))

    def __init__(self, *, data: Any = None, get_position: Any = None, get_color: Any = (0, 0, 0, 255), get_normal: Any = None, point_size: float = 10, **kwargs: Any) -> None:
        super().__init__(
            data=data,
            get_position=get_position,
            get_color=list(get_color) if isinstance(get_color, tuple) else get_color,
            get_normal=get_normal,
            point_size=point_size,
            **kwargs,
        )


@_experimental
class SolidPolygonLayer(BaseLayer):
    """Render solid polygons (no stroke, better performance than PolygonLayer)."""

    LAYER_TYPE = "SolidPolygonLayer"

    def __init__(self, *, data: Any = None, get_polygon: Any = None, get_fill_color: Any = (0, 0, 0, 255), extruded: bool = False, get_elevation: Any = 1000, **kwargs: Any) -> None:
        super().__init__(
            data=data,
            get_polygon=get_polygon,
            get_fill_color=list(get_fill_color) if isinstance(get_fill_color, tuple) else get_fill_color,
            extruded=extruded,
            get_elevation=get_elevation,
            **kwargs,
        )
