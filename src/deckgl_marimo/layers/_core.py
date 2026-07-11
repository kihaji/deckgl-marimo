"""Core deck.gl layer wrappers."""

from __future__ import annotations

import warnings
from typing import Any

from deckgl_marimo._accessors import Accessor, ColorAccessor, PositionAccessor
from deckgl_marimo._base import MAX_SAFE_INTEGER, BaseLayer
from deckgl_marimo.layers._binary_attrs import (
    BinaryAttr,
    BinaryAttributesMixin,
    strip_binary_accessors,
)


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


class ScatterplotLayer(BinaryAttributesMixin, BaseLayer):
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

    BINARY_ATTRIBUTES = (
        BinaryAttr("getPosition", "positions", "get_position", "position", required=True),
        BinaryAttr("getFillColor", "colors", "get_fill_color", "color"),
        BinaryAttr("getRadius", "radii", "get_radius", "value"),
    )

    def __init__(
        self,
        *,
        data: Any = None,
        get_position: PositionAccessor | None = None,
        get_fill_color: ColorAccessor = (0, 0, 0, 255),
        get_line_color: ColorAccessor = (0, 0, 0, 255),
        get_radius: Accessor = 1,
        get_line_width: Accessor = 1,
        radius_units: str = "meters",
        radius_scale: float = 1,
        radius_min_pixels: float = 0,
        radius_max_pixels: float = MAX_SAFE_INTEGER,
        line_width_units: str = "meters",
        line_width_scale: float = 1,
        line_width_min_pixels: float = 0,
        line_width_max_pixels: float = MAX_SAFE_INTEGER,
        stroked: bool = False,
        filled: bool = True,
        billboard: bool = False,
        antialiasing: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=data,
            get_position=get_position,
            get_fill_color=get_fill_color,
            get_line_color=get_line_color,
            get_radius=get_radius,
            get_line_width=get_line_width,
            radius_units=radius_units,
            radius_scale=radius_scale,
            radius_min_pixels=radius_min_pixels,
            radius_max_pixels=radius_max_pixels,
            line_width_units=line_width_units,
            line_width_scale=line_width_scale,
            line_width_min_pixels=line_width_min_pixels,
            line_width_max_pixels=line_width_max_pixels,
            stroked=stroked,
            filled=filled,
            billboard=billboard,
            antialiasing=antialiasing,
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
        get_fill_color: ColorAccessor = (0, 0, 0, 255),
        get_line_color: ColorAccessor = (0, 0, 0, 255),
        get_line_width: Accessor = 1,
        get_point_radius: Accessor = 1,
        get_elevation: Accessor = 1000,
        filled: bool = True,
        stroked: bool = True,
        extruded: bool = False,
        wireframe: bool = False,
        point_type: str = "circle",
        elevation_scale: float = 1,
        line_width_units: str = "meters",
        line_width_scale: float = 1,
        line_width_min_pixels: float = 0,
        line_joint_rounded: bool = False,
        line_miter_limit: float = 4,
        line_cap_rounded: bool = False,
        line_billboard: bool = False,
        point_antialiasing: bool = True,
        point_billboard: bool = True,
        text_background: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=data,
            get_fill_color=get_fill_color,
            get_line_color=get_line_color,
            get_line_width=get_line_width,
            get_point_radius=get_point_radius,
            get_elevation=get_elevation,
            filled=filled,
            stroked=stroked,
            extruded=extruded,
            wireframe=wireframe,
            point_type=point_type,
            elevation_scale=elevation_scale,
            line_width_units=line_width_units,
            line_width_scale=line_width_scale,
            line_width_min_pixels=line_width_min_pixels,
            line_joint_rounded=line_joint_rounded,
            line_miter_limit=line_miter_limit,
            line_cap_rounded=line_cap_rounded,
            line_billboard=line_billboard,
            point_antialiasing=point_antialiasing,
            point_billboard=point_billboard,
            text_background=text_background,
            **kwargs,
        )


class ArcLayer(BinaryAttributesMixin, BaseLayer):
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

    BINARY_ATTRIBUTES = (
        BinaryAttr("getSourcePosition", "source_positions", "get_source_position", "position", required=True),
        BinaryAttr("getTargetPosition", "target_positions", "get_target_position", "position", required=True),
        BinaryAttr("getSourceColor", "source_colors", "get_source_color", "color"),
        BinaryAttr("getTargetColor", "target_colors", "get_target_color", "color"),
    )

    def __init__(
        self,
        *,
        data: Any = None,
        get_source_position: PositionAccessor | None = None,
        get_target_position: PositionAccessor | None = None,
        get_source_color: ColorAccessor = (0, 0, 255, 255),
        get_target_color: ColorAccessor = (0, 200, 0, 255),
        get_width: Accessor = 1,
        get_height: Accessor = 1,
        get_tilt: Accessor = 0,
        great_circle: bool = False,
        num_segments: int = 50,
        width_units: str = "pixels",
        width_scale: float = 1,
        width_min_pixels: float = 0,
        width_max_pixels: float = MAX_SAFE_INTEGER,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=data,
            get_source_position=get_source_position,
            get_target_position=get_target_position,
            get_source_color=get_source_color,
            get_target_color=get_target_color,
            get_width=get_width,
            get_height=get_height,
            get_tilt=get_tilt,
            great_circle=great_circle,
            num_segments=num_segments,
            width_units=width_units,
            width_scale=width_scale,
            width_min_pixels=width_min_pixels,
            width_max_pixels=width_max_pixels,
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

    def __init__(
        self,
        *,
        data: Any = None,
        get_path: PositionAccessor | None = None,
        get_color: ColorAccessor = (0, 0, 0, 255),
        get_width: Accessor = 1,
        width_units: str = "meters",
        width_scale: float = 1,
        width_min_pixels: float = 0,
        width_max_pixels: float = MAX_SAFE_INTEGER,
        rounded: bool = False,
        joint_rounded: bool = False,
        cap_rounded: bool = False,
        miter_limit: float = 4,
        billboard: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=data,
            get_path=get_path,
            get_color=get_color,
            get_width=get_width,
            width_units=width_units,
            width_scale=width_scale,
            width_min_pixels=width_min_pixels,
            width_max_pixels=width_max_pixels,
            rounded=rounded,
            joint_rounded=joint_rounded,
            cap_rounded=cap_rounded,
            miter_limit=miter_limit,
            billboard=billboard,
            **kwargs,
        )

    def to_spec(self) -> dict:
        spec = super().to_spec()
        if self.use_binary:
            strip_binary_accessors(spec, ("getPath", "getColor"))
        return spec

    def to_binary(self) -> tuple[dict, bytes] | None:
        """Pack path data (variable-length geometry) into binary format."""
        if not self.use_binary or self.data is None:
            return None
        from deckgl_marimo._binary import pack_binary
        from deckgl_marimo._color_scale import resolve_color_accessor
        import numpy as np

        # Fast path: pre-built numpy arrays
        if isinstance(self.data, dict) and "path_coords" in self.data:
            data = self.data
            si = np.asarray(data["start_indices"], dtype=np.uint32)
            n = len(si)
            attrs: dict[str, tuple[Any, str, int]] = {
                "getPath": (data["path_coords"], "float32", 2),
            }
            if data.get("colors") is not None:
                attrs["getColor"] = (data["colors"], "uint8", 4)
            meta, buf = pack_binary(n, attrs, start_indices=si)
            meta["id"] = self.id
            return meta, buf

        # Slow path: list of dicts
        if not isinstance(self.data, list):
            return None
        rows = self.data
        n = len(rows)
        path_key = self._props.get("get_path") or "path"
        if not isinstance(path_key, str):
            return None

        vert_counts = np.array([len(row[path_key]) for row in rows], dtype=np.uint32)
        si = np.empty(n, dtype=np.uint32)
        si[0] = 0
        np.cumsum(vert_counts[:-1], out=si[1:])

        path_flat = np.concatenate(
            [np.asarray(row[path_key], dtype=np.float32).reshape(-1, 2) for row in rows]
        )

        attrs = {"getPath": (path_flat, "float32", 2)}

        # One color per path, repeated for each of its vertices
        color_key = self._props.get("get_color")
        rgba = None
        if isinstance(color_key, str):
            rgba = np.empty((n, 4), dtype=np.uint8)
            for i, row in enumerate(rows):
                c = row[color_key]
                rgba[i] = (c[0], c[1], c[2], c[3] if len(c) > 3 else 255)
        else:
            resolved = resolve_color_accessor(color_key, rows, n)
            if resolved is not None:
                rgba = np.asarray(resolved, dtype=np.uint8)
        if rgba is not None:
            attrs["getColor"] = (np.repeat(rgba, vert_counts, axis=0), "uint8", 4)

        meta, buf = pack_binary(n, attrs, start_indices=si)
        meta["id"] = self.id
        return meta, buf


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
    line_width_units
        Units for line width: ``"meters"`` (default), ``"common"``, or ``"pixels"``.
    line_width_scale
        Global line width multiplier.
    line_width_min_pixels
        Minimum line width in pixels.
    line_width_max_pixels
        Maximum line width in pixels.
    wireframe
        Whether to draw the wireframe of extruded polygons.

    Notes
    -----
    With ``use_binary=True``, the emitted layer spec switches to
    deck.gl's ``SolidPolygonLayer`` because the composite
    ``PolygonLayer`` does not support binary attributes. Stroke
    (``stroked``, ``get_line_color``, ``get_line_width``) is not
    rendered in binary mode.
    """

    LAYER_TYPE = "PolygonLayer"

    def __init__(
        self,
        *,
        data: Any = None,
        get_polygon: PositionAccessor | None = None,
        get_fill_color: ColorAccessor = (0, 0, 0, 255),
        get_line_color: ColorAccessor = (0, 0, 0, 255),
        get_line_width: Accessor = 1,
        filled: bool = True,
        stroked: bool = True,
        extruded: bool = False,
        get_elevation: Accessor = 1000,
        elevation_scale: float = 1,
        line_width_units: str = "meters",
        line_width_scale: float = 1,
        line_width_min_pixels: float = 0,
        line_width_max_pixels: float = MAX_SAFE_INTEGER,
        line_joint_rounded: bool = False,
        line_miter_limit: float = 4,
        wireframe: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=data,
            get_polygon=get_polygon,
            get_fill_color=get_fill_color,
            get_line_color=get_line_color,
            get_line_width=get_line_width,
            filled=filled,
            stroked=stroked,
            extruded=extruded,
            get_elevation=get_elevation,
            elevation_scale=elevation_scale,
            line_width_units=line_width_units,
            line_width_scale=line_width_scale,
            line_width_min_pixels=line_width_min_pixels,
            line_width_max_pixels=line_width_max_pixels,
            line_joint_rounded=line_joint_rounded,
            line_miter_limit=line_miter_limit,
            wireframe=wireframe,
            **kwargs,
        )

    def to_spec(self) -> dict:
        """Serialize to spec. Uses SolidPolygonLayer for binary mode."""
        spec = super().to_spec()
        if self.use_binary:
            # PolygonLayer is a composite layer that calls getPolygon(d)
            # internally — it doesn't support binary data.attributes.
            # SolidPolygonLayer is the underlying primitive that does.
            spec["type"] = "SolidPolygonLayer"
            spec.pop("getPolygon", None)
            strip_binary_accessors(spec, ("getFillColor",))
        return spec

    def to_binary(self) -> tuple[dict, bytes] | None:
        """Pack polygon data into binary format."""
        if not self.use_binary or self.data is None:
            return None
        if not isinstance(self.data, list):
            return None

        from deckgl_marimo._binary import pack_polygon_binary
        from deckgl_marimo._color_scale import resolve_color_accessor

        get_polygon = self._props.get("get_polygon") or "polygon"
        if not isinstance(get_polygon, str):
            # Binary packing reads polygon vertices from a single column;
            # multi-column position accessors are not supported here.
            return None
        get_fill_color = self._props.get("get_fill_color")

        if isinstance(get_fill_color, str):
            meta, buf = pack_polygon_binary(self.data, get_polygon, get_fill_color)
        else:
            # ColorScale/callable: resolve to per-polygon colors; expansion
            # to per-vertex happens inside pack_polygon_binary. A constant
            # color resolves to None and stays in the spec instead.
            resolved = resolve_color_accessor(get_fill_color, self.data, len(self.data))
            meta, buf = pack_polygon_binary(
                self.data, get_polygon, None, per_polygon_colors=resolved
            )

        meta["id"] = self.id
        return meta, buf


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
        get_position: PositionAccessor | None = None,
        get_icon: Accessor | None = None,
        get_size: Accessor = 1,
        get_color: ColorAccessor = (0, 0, 0, 255),
        get_angle: Accessor = 0,
        get_pixel_offset: Accessor = (0, 0),
        icon_atlas: str | None = None,
        icon_mapping: dict | None = None,
        size_units: str = "pixels",
        size_scale: float = 1,
        size_min_pixels: float = 0,
        size_max_pixels: float = MAX_SAFE_INTEGER,
        alpha_cutoff: float = 0.05,
        billboard: bool = True,
        **kwargs: Any,
    ) -> None:
        props: dict[str, Any] = {
            "get_position": get_position,
            "get_icon": get_icon,
            "get_size": get_size,
            "get_color": get_color,
            "get_angle": get_angle,
            "get_pixel_offset": get_pixel_offset,
            "size_units": size_units,
            "size_scale": size_scale,
            "size_min_pixels": size_min_pixels,
            "size_max_pixels": size_max_pixels,
            "alpha_cutoff": alpha_cutoff,
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
        get_position: PositionAccessor | None = None,
        get_text: Accessor | None = None,
        get_size: Accessor = 32,
        get_color: ColorAccessor = (0, 0, 0, 255),
        get_angle: Accessor = 0,
        get_alignment_baseline: str = "center",
        get_text_anchor: str = "middle",
        get_pixel_offset: Accessor = (0, 0),
        get_background_color: ColorAccessor = (255, 255, 255, 255),
        get_border_color: ColorAccessor = (0, 0, 0, 255),
        get_border_width: Accessor = 0,
        font_family: str = "Monaco, monospace",
        size_units: str = "pixels",
        size_scale: float = 1,
        size_min_pixels: float = 0,
        size_max_pixels: float = MAX_SAFE_INTEGER,
        billboard: bool = True,
        background: bool = False,
        background_padding: tuple[float, float, float, float] = (0, 0, 0, 0),
        outline_width: float = 0,
        outline_color: tuple[int, int, int, int] = (0, 0, 0, 255),
        word_break: str = "break-word",
        max_width: float = -1,
        line_height: float = 1.0,
        character_set: Any = None,
        **kwargs: Any,
    ) -> None:
        props: dict[str, Any] = {
            "get_position": get_position,
            "get_text": get_text,
            "get_size": get_size,
            "get_color": get_color,
            "get_angle": get_angle,
            "get_alignment_baseline": get_alignment_baseline,
            "get_text_anchor": get_text_anchor,
            "get_pixel_offset": get_pixel_offset,
            "get_background_color": get_background_color,
            "get_border_color": get_border_color,
            "get_border_width": get_border_width,
            "font_family": font_family,
            "size_units": size_units,
            "size_scale": size_scale,
            "size_min_pixels": size_min_pixels,
            "size_max_pixels": size_max_pixels,
            "billboard": billboard,
            "background": background,
            "background_padding": background_padding,
            "outline_width": outline_width,
            "outline_color": outline_color,
            "word_break": word_break,
            "max_width": max_width,
            "line_height": line_height,
        }
        if character_set is not None:
            props["character_set"] = character_set
        super().__init__(data=data, **props, **kwargs)


class ColumnLayer(BinaryAttributesMixin, BaseLayer):
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

    BINARY_ATTRIBUTES = (
        BinaryAttr("getPosition", "positions", "get_position", "position", required=True),
        BinaryAttr("getFillColor", "colors", "get_fill_color", "color"),
        BinaryAttr("getElevation", "elevations", "get_elevation", "value"),
    )

    def __init__(
        self,
        *,
        data: Any = None,
        get_position: PositionAccessor | None = None,
        get_fill_color: ColorAccessor = (255, 0, 0, 255),
        get_line_color: ColorAccessor = (0, 0, 0, 255),
        get_elevation: Accessor = 1000,
        get_line_width: Accessor = 1,
        disk_resolution: int = 20,
        radius: float = 1000,
        radius_units: str = "meters",
        angle: float = 0,
        offset: tuple[float, float] = (0, 0),
        coverage: float = 1,
        elevation_scale: float = 1,
        line_width_units: str = "meters",
        line_width_scale: float = 1,
        line_width_min_pixels: float = 0,
        line_width_max_pixels: float = MAX_SAFE_INTEGER,
        extruded: bool = True,
        filled: bool = True,
        stroked: bool = False,
        wireframe: bool = False,
        flat_shading: bool = False,
        vertices: list | None = None,
        **kwargs: Any,
    ) -> None:
        props: dict[str, Any] = {
            "get_position": get_position,
            "get_fill_color": get_fill_color,
            "get_line_color": get_line_color,
            "get_elevation": get_elevation,
            "get_line_width": get_line_width,
            "disk_resolution": disk_resolution,
            "radius": radius,
            "radius_units": radius_units,
            "angle": angle,
            "offset": offset,
            "coverage": coverage,
            "elevation_scale": elevation_scale,
            "line_width_units": line_width_units,
            "line_width_scale": line_width_scale,
            "line_width_min_pixels": line_width_min_pixels,
            "line_width_max_pixels": line_width_max_pixels,
            "extruded": extruded,
            "filled": filled,
            "stroked": stroked,
            "wireframe": wireframe,
            "flat_shading": flat_shading,
        }
        if vertices is not None:
            props["vertices"] = vertices
        super().__init__(data=data, **props, **kwargs)


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


class LineLayer(BinaryAttributesMixin, BaseLayer):
    """Render straight lines between pairs of points."""

    LAYER_TYPE = "LineLayer"

    BINARY_ATTRIBUTES = (
        BinaryAttr("getSourcePosition", "source_positions", "get_source_position", "position", required=True),
        BinaryAttr("getTargetPosition", "target_positions", "get_target_position", "position", required=True),
        BinaryAttr("getColor", "colors", "get_color", "color"),
    )

    def __init__(
        self,
        *,
        data: Any = None,
        get_source_position: PositionAccessor | None = None,
        get_target_position: PositionAccessor | None = None,
        get_color: ColorAccessor = (0, 0, 0, 255),
        get_width: Accessor = 1,
        width_units: str = "pixels",
        width_scale: float = 1,
        width_min_pixels: float = 0,
        width_max_pixels: float = MAX_SAFE_INTEGER,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=data,
            get_source_position=get_source_position,
            get_target_position=get_target_position,
            get_color=get_color,
            get_width=get_width,
            width_units=width_units,
            width_scale=width_scale,
            width_min_pixels=width_min_pixels,
            width_max_pixels=width_max_pixels,
            **kwargs,
        )


class PointCloudLayer(BinaryAttributesMixin, BaseLayer):
    """Render a point cloud."""

    LAYER_TYPE = "PointCloudLayer"

    BINARY_ATTRIBUTES = (
        BinaryAttr("getPosition", "positions", "get_position", "position", required=True),
        BinaryAttr("getColor", "colors", "get_color", "color"),
        BinaryAttr("getNormal", "normals", "get_normal", "value"),
    )

    def __init__(
        self,
        *,
        data: Any = None,
        get_position: PositionAccessor | None = None,
        get_color: ColorAccessor = (0, 0, 0, 255),
        get_normal: Accessor | None = None,
        point_size: float = 10,
        size_units: str = "pixels",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=data,
            get_position=get_position,
            get_color=get_color,
            get_normal=get_normal,
            point_size=point_size,
            size_units=size_units,
            **kwargs,
        )


class SolidPolygonLayer(BaseLayer):
    """Render solid polygons (no stroke, better performance than PolygonLayer)."""

    LAYER_TYPE = "SolidPolygonLayer"

    def __init__(
        self,
        *,
        data: Any = None,
        get_polygon: PositionAccessor | None = None,
        get_fill_color: ColorAccessor = (0, 0, 0, 255),
        get_line_color: ColorAccessor = (0, 0, 0, 255),
        get_elevation: Accessor = 1000,
        filled: bool = True,
        extruded: bool = False,
        wireframe: bool = False,
        elevation_scale: float = 1,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=data,
            get_polygon=get_polygon,
            get_fill_color=get_fill_color,
            get_line_color=get_line_color,
            get_elevation=get_elevation,
            filled=filled,
            extruded=extruded,
            wireframe=wireframe,
            elevation_scale=elevation_scale,
            **kwargs,
        )
