"""Core deck.gl layer wrappers."""

from __future__ import annotations

import warnings
from typing import Any

from deckgl_marimo._base import BaseLayer


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
        self._get_position_key = get_position
        self._get_fill_color_key = get_fill_color
        self._get_radius_key = get_radius
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

    def to_spec(self) -> dict:
        spec = super().to_spec()
        if self.use_binary:
            # Strip accessor props that binary data provides
            for key in ("getPosition", "getFillColor", "getRadius"):
                val = spec.get(key)
                if isinstance(val, str):
                    spec.pop(key, None)
                elif isinstance(val, list) and all(isinstance(x, str) for x in val):
                    spec.pop(key, None)
        return spec

    def to_binary(self) -> tuple[dict, bytes] | None:
        if not self.use_binary or self.data is None:
            return None
        from deckgl_marimo._binary import pack_binary
        import numpy as np

        data = self.data if isinstance(self.data, dict) else None

        # Fast path: pre-built numpy arrays
        if data and "positions" in data:
            n = len(data["positions"])
            attrs: dict[str, tuple[Any, str, int]] = {
                "getPosition": (data["positions"], "float32", 2),
            }
            if data.get("colors") is not None:
                attrs["getFillColor"] = (data["colors"], "uint8", 4)
            if data.get("radii") is not None:
                attrs["getRadius"] = (data["radii"], "float32", 1)
            meta, buf = pack_binary(n, attrs)
            meta["id"] = self.id
            return meta, buf

        # Slow path: list of dicts
        if not isinstance(self.data, list):
            return None
        n = len(self.data)
        pos_key = self._get_position_key
        if isinstance(pos_key, list):
            positions = np.array([[row[pos_key[0]], row[pos_key[1]]] for row in self.data], dtype=np.float32)
        elif isinstance(pos_key, str):
            positions = np.array([row[pos_key] for row in self.data], dtype=np.float32)
        else:
            return None

        attrs = {"getPosition": (positions, "float32", 2)}

        if isinstance(self._get_fill_color_key, str):
            colors = np.array([row[self._get_fill_color_key] for row in self.data], dtype=np.uint8)
            if colors.shape[1] == 3:
                alpha = np.full((n, 1), 255, dtype=np.uint8)
                colors = np.hstack([colors, alpha])
            attrs["getFillColor"] = (colors, "uint8", 4)

        if isinstance(self._get_radius_key, str):
            radii = np.array([row[self._get_radius_key] for row in self.data], dtype=np.float32)
            attrs["getRadius"] = (radii, "float32", 1)

        meta, buf = pack_binary(n, attrs)
        meta["id"] = self.id
        return meta, buf


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
        self._get_source_position_key = get_source_position
        self._get_target_position_key = get_target_position
        self._get_source_color_key = get_source_color
        self._get_target_color_key = get_target_color
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

    def to_spec(self) -> dict:
        spec = super().to_spec()
        if self.use_binary:
            for key in ("getSourcePosition", "getTargetPosition",
                       "getSourceColor", "getTargetColor"):
                val = spec.get(key)
                if isinstance(val, str) or (isinstance(val, list) and all(isinstance(x, str) for x in val)):
                    spec.pop(key, None)
        return spec

    def to_binary(self) -> tuple[dict, bytes] | None:
        if not self.use_binary or self.data is None:
            return None
        from deckgl_marimo._binary import pack_binary
        import numpy as np

        # Fast path
        if isinstance(self.data, dict) and "source_positions" in self.data:
            d = self.data
            n = len(d["source_positions"])
            attrs: dict[str, tuple[Any, str, int]] = {
                "getSourcePosition": (d["source_positions"], "float32", 2),
                "getTargetPosition": (d["target_positions"], "float32", 2),
            }
            if d.get("source_colors") is not None:
                attrs["getSourceColor"] = (d["source_colors"], "uint8", 4)
            if d.get("target_colors") is not None:
                attrs["getTargetColor"] = (d["target_colors"], "uint8", 4)
            meta, buf = pack_binary(n, attrs)
            meta["id"] = self.id
            return meta, buf

        # Slow path
        if not isinstance(self.data, list):
            return None
        n = len(self.data)

        def _extract_pos(key):
            if isinstance(key, list):
                return np.array([[row[key[0]], row[key[1]]] for row in self.data], dtype=np.float32)
            elif isinstance(key, str):
                return np.array([row[key] for row in self.data], dtype=np.float32)
            return None

        src = _extract_pos(self._get_source_position_key)
        tgt = _extract_pos(self._get_target_position_key)
        if src is None or tgt is None:
            return None

        attrs = {
            "getSourcePosition": (src, "float32", 2),
            "getTargetPosition": (tgt, "float32", 2),
        }

        if isinstance(self._get_source_color_key, str):
            sc = np.array([row[self._get_source_color_key] for row in self.data], dtype=np.uint8)
            if sc.ndim == 2 and sc.shape[1] == 3:
                sc = np.hstack([sc, np.full((n, 1), 255, dtype=np.uint8)])
            attrs["getSourceColor"] = (sc, "uint8", 4)

        if isinstance(self._get_target_color_key, str):
            tc = np.array([row[self._get_target_color_key] for row in self.data], dtype=np.uint8)
            if tc.ndim == 2 and tc.shape[1] == 3:
                tc = np.hstack([tc, np.full((n, 1), 255, dtype=np.uint8)])
            attrs["getTargetColor"] = (tc, "uint8", 4)

        meta, buf = pack_binary(n, attrs)
        meta["id"] = self.id
        return meta, buf


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
        get_path: Any = None,
        get_color: Any = (0, 0, 0, 255),
        get_width: Any = 1,
        width_scale: float = 1,
        width_min_pixels: float = 0,
        rounded: bool = False,
        billboard: bool = False,
        **kwargs: Any,
    ) -> None:
        self._get_path_key = get_path
        self._get_color_key = get_color
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

    def to_spec(self) -> dict:
        spec = super().to_spec()
        if self.use_binary:
            if isinstance(spec.get("getPath"), str):
                spec.pop("getPath", None)
            if isinstance(self._get_color_key, str):
                spec.pop("getColor", None)
        return spec

    def to_binary(self) -> tuple[dict, bytes] | None:
        if not self.use_binary or self.data is None:
            return None
        from deckgl_marimo._binary import pack_binary
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
        n = len(self.data)
        path_key = self._get_path_key or "path"

        vert_counts = np.array([len(row[path_key]) for row in self.data], dtype=np.uint32)
        total_verts = int(vert_counts.sum())
        si = np.empty(n, dtype=np.uint32)
        si[0] = 0
        np.cumsum(vert_counts[:-1], out=si[1:])

        path_flat = np.empty(total_verts * 2, dtype=np.float32)
        idx = 0
        for row in self.data:
            for pt in row[path_key]:
                path_flat[idx] = pt[0]
                path_flat[idx + 1] = pt[1]
                idx += 2

        attrs = {"getPath": (path_flat, "float32", 2)}

        if isinstance(self._get_color_key, str):
            vertex_colors = np.empty((total_verts, 4), dtype=np.uint8)
            for i, row in enumerate(self.data):
                c = row[self._get_color_key]
                rgba = (c[0], c[1], c[2], c[3] if len(c) > 3 else 255)
                v_start = si[i]
                v_end = si[i + 1] if i + 1 < n else total_verts
                vertex_colors[v_start:v_end] = rgba
            attrs["getColor"] = (vertex_colors, "uint8", 4)

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
    """

    LAYER_TYPE = "PolygonLayer"

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
        self._get_polygon_key = get_polygon
        self._get_fill_color_key = get_fill_color
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

    def to_spec(self) -> dict:
        """Serialize to spec. Uses SolidPolygonLayer for binary mode."""
        spec = super().to_spec()
        if self.use_binary:
            # PolygonLayer is a composite layer that calls getPolygon(d)
            # internally — it doesn't support binary data.attributes.
            # SolidPolygonLayer is the underlying primitive that does.
            spec["type"] = "SolidPolygonLayer"
            # Remove accessor props that are handled by binary attributes
            spec.pop("getPolygon", None)
            if isinstance(self._get_fill_color_key, str):
                spec.pop("getFillColor", None)
        return spec

    def to_binary(self) -> tuple[dict, bytes] | None:
        """Pack polygon data into binary format."""
        if not self.use_binary or self.data is None:
            return None
        if not isinstance(self.data, list):
            return None

        from deckgl_marimo._binary import pack_polygon_binary

        get_polygon = self._get_polygon_key or "polygon"
        get_fill_color = self._get_fill_color_key
        # Only pass color key if it's an accessor (string column name)
        color_arg = get_fill_color if isinstance(get_fill_color, str) else None

        meta, buf = pack_polygon_binary(self.data, get_polygon, color_arg)
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
        self._get_position_key = get_position
        self._get_fill_color_key = get_fill_color
        self._get_elevation_key = get_elevation
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

    def to_spec(self) -> dict:
        spec = super().to_spec()
        if self.use_binary:
            for key in ("getPosition", "getFillColor", "getElevation"):
                val = spec.get(key)
                if isinstance(val, str) or (isinstance(val, list) and all(isinstance(x, str) for x in val)):
                    spec.pop(key, None)
        return spec

    def to_binary(self) -> tuple[dict, bytes] | None:
        if not self.use_binary or self.data is None:
            return None
        from deckgl_marimo._binary import pack_binary
        import numpy as np

        if isinstance(self.data, dict) and "positions" in self.data:
            d = self.data
            n = len(d["positions"])
            attrs: dict[str, tuple[Any, str, int]] = {
                "getPosition": (d["positions"], "float32", 2),
            }
            if d.get("colors") is not None:
                attrs["getFillColor"] = (d["colors"], "uint8", 4)
            if d.get("elevations") is not None:
                attrs["getElevation"] = (d["elevations"], "float32", 1)
            meta, buf = pack_binary(n, attrs)
            meta["id"] = self.id
            return meta, buf

        if not isinstance(self.data, list):
            return None
        n = len(self.data)
        pos_key = self._get_position_key

        if isinstance(pos_key, list):
            positions = np.array([[row[pos_key[0]], row[pos_key[1]]] for row in self.data], dtype=np.float32)
        elif isinstance(pos_key, str):
            positions = np.array([row[pos_key] for row in self.data], dtype=np.float32)
        else:
            return None

        attrs = {"getPosition": (positions, "float32", 2)}

        if isinstance(self._get_fill_color_key, str):
            colors = np.array([row[self._get_fill_color_key] for row in self.data], dtype=np.uint8)
            if colors.ndim == 2 and colors.shape[1] == 3:
                colors = np.hstack([colors, np.full((n, 1), 255, dtype=np.uint8)])
            attrs["getFillColor"] = (colors, "uint8", 4)

        if isinstance(self._get_elevation_key, str):
            elevations = np.array([row[self._get_elevation_key] for row in self.data], dtype=np.float32)
            attrs["getElevation"] = (elevations, "float32", 1)

        meta, buf = pack_binary(n, attrs)
        meta["id"] = self.id
        return meta, buf


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
        self._get_source_position_key = get_source_position
        self._get_target_position_key = get_target_position
        self._get_color_key = get_color
        super().__init__(
            data=data,
            get_source_position=get_source_position,
            get_target_position=get_target_position,
            get_color=list(get_color) if isinstance(get_color, tuple) else get_color,
            get_width=get_width,
            **kwargs,
        )

    def to_spec(self) -> dict:
        spec = super().to_spec()
        if self.use_binary:
            for key in ("getSourcePosition", "getTargetPosition", "getColor"):
                val = spec.get(key)
                if isinstance(val, str) or (isinstance(val, list) and all(isinstance(x, str) for x in val)):
                    spec.pop(key, None)
        return spec

    def to_binary(self) -> tuple[dict, bytes] | None:
        if not self.use_binary or self.data is None:
            return None
        from deckgl_marimo._binary import pack_binary
        import numpy as np

        if isinstance(self.data, dict) and "source_positions" in self.data:
            d = self.data
            n = len(d["source_positions"])
            attrs: dict[str, tuple[Any, str, int]] = {
                "getSourcePosition": (d["source_positions"], "float32", 2),
                "getTargetPosition": (d["target_positions"], "float32", 2),
            }
            if d.get("colors") is not None:
                attrs["getColor"] = (d["colors"], "uint8", 4)
            meta, buf = pack_binary(n, attrs)
            meta["id"] = self.id
            return meta, buf

        if not isinstance(self.data, list):
            return None
        n = len(self.data)

        def _extract_pos(key):
            if isinstance(key, list):
                return np.array([[row[key[0]], row[key[1]]] for row in self.data], dtype=np.float32)
            elif isinstance(key, str):
                return np.array([row[key] for row in self.data], dtype=np.float32)
            return None

        src = _extract_pos(self._get_source_position_key)
        tgt = _extract_pos(self._get_target_position_key)
        if src is None or tgt is None:
            return None

        attrs = {
            "getSourcePosition": (src, "float32", 2),
            "getTargetPosition": (tgt, "float32", 2),
        }
        if isinstance(self._get_color_key, str):
            colors = np.array([row[self._get_color_key] for row in self.data], dtype=np.uint8)
            if colors.ndim == 2 and colors.shape[1] == 3:
                colors = np.hstack([colors, np.full((n, 1), 255, dtype=np.uint8)])
            attrs["getColor"] = (colors, "uint8", 4)

        meta, buf = pack_binary(n, attrs)
        meta["id"] = self.id
        return meta, buf


@_experimental
class PointCloudLayer(BaseLayer):
    """Render a point cloud."""

    LAYER_TYPE = "PointCloudLayer"

    def __init__(self, *, data: Any = None, get_position: Any = None, get_color: Any = (0, 0, 0, 255), get_normal: Any = None, point_size: float = 10, **kwargs: Any) -> None:
        self._get_position_key = get_position
        self._get_color_key = get_color
        self._get_normal_key = get_normal
        super().__init__(
            data=data,
            get_position=get_position,
            get_color=list(get_color) if isinstance(get_color, tuple) else get_color,
            get_normal=get_normal,
            point_size=point_size,
            **kwargs,
        )

    def to_spec(self) -> dict:
        spec = super().to_spec()
        if self.use_binary:
            for key in ("getPosition", "getColor", "getNormal"):
                val = spec.get(key)
                if isinstance(val, str) or (isinstance(val, list) and all(isinstance(x, str) for x in val)):
                    spec.pop(key, None)
        return spec

    def to_binary(self) -> tuple[dict, bytes] | None:
        if not self.use_binary or self.data is None:
            return None
        from deckgl_marimo._binary import pack_binary
        import numpy as np

        if isinstance(self.data, dict) and "positions" in self.data:
            d = self.data
            n = len(d["positions"])
            pos_size = 3 if d["positions"].shape[1] == 3 else 2
            attrs: dict[str, tuple[Any, str, int]] = {
                "getPosition": (d["positions"], "float32", pos_size),
            }
            if d.get("colors") is not None:
                attrs["getColor"] = (d["colors"], "uint8", 4)
            if d.get("normals") is not None:
                attrs["getNormal"] = (d["normals"], "float32", 3)
            meta, buf = pack_binary(n, attrs)
            meta["id"] = self.id
            return meta, buf

        if not isinstance(self.data, list):
            return None
        n = len(self.data)
        pos_key = self._get_position_key
        if isinstance(pos_key, list):
            positions = np.array([[row[k] for k in pos_key] for row in self.data], dtype=np.float32)
        elif isinstance(pos_key, str):
            positions = np.array([row[pos_key] for row in self.data], dtype=np.float32)
        else:
            return None

        pos_size = positions.shape[1] if positions.ndim == 2 else 3
        attrs = {"getPosition": (positions, "float32", pos_size)}

        if isinstance(self._get_color_key, str):
            colors = np.array([row[self._get_color_key] for row in self.data], dtype=np.uint8)
            if colors.ndim == 2 and colors.shape[1] == 3:
                colors = np.hstack([colors, np.full((n, 1), 255, dtype=np.uint8)])
            attrs["getColor"] = (colors, "uint8", 4)

        if isinstance(self._get_normal_key, str):
            normals = np.array([row[self._get_normal_key] for row in self.data], dtype=np.float32)
            attrs["getNormal"] = (normals, "float32", 3)

        meta, buf = pack_binary(n, attrs)
        meta["id"] = self.id
        return meta, buf


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
