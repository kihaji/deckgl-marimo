"""Composite deck.gl layers that decompose into multiple sub-layers."""

from __future__ import annotations

import math
from typing import Any

from deckgl_marimo._accessors import Accessor, ColorAccessor
from deckgl_marimo._base import BaseLayer
from deckgl_marimo._data import prepare_data
from deckgl_marimo.layers._core import ArcLayer, PolygonLayer, ScatterplotLayer

_METERS_PER_DEG_LAT = 111_320
_UNIT_TO_METERS = {
    "meters": 1.0,
    "kilometers": 1_000.0,
    "nautical_miles": 1_852.0,
}


def _compute_ellipse_ring(
    center_lon: float,
    center_lat: float,
    semi_major_m: float,
    semi_minor_m: float,
    orientation_rad: float,
    num_vertices: int,
) -> list[list[float]]:
    """Compute a closed polygon ring approximating an ellipse.

    Parameters
    ----------
    center_lon, center_lat
        Center of the ellipse in decimal degrees.
    semi_major_m, semi_minor_m
        Semi-major and semi-minor axis lengths in meters.
    orientation_rad
        Orientation in radians. 0 = major axis points north,
        increasing clockwise (geographic convention).
    num_vertices
        Number of vertices in the ring (the returned list has
        ``num_vertices + 1`` entries because the ring is closed).

    Returns
    -------
    list[list[float]]
        Coordinate ring as ``[[lon, lat], ...]`` with first == last.
    """
    lat_rad = math.radians(center_lat)
    cos_lat = math.cos(lat_rad)
    deg_per_m_lat = 1.0 / _METERS_PER_DEG_LAT
    deg_per_m_lon = 1.0 / (_METERS_PER_DEG_LAT * cos_lat) if cos_lat > 1e-10 else 0.0

    cos_o = math.cos(orientation_rad)
    sin_o = math.sin(orientation_rad)

    ring: list[list[float]] = []
    for i in range(num_vertices):
        theta = 2.0 * math.pi * i / num_vertices
        # Unrotated: major axis along north (y), minor along east (x)
        x_m = semi_minor_m * math.cos(theta)
        y_m = semi_major_m * math.sin(theta)
        # Rotate clockwise by orientation (north → east)
        x_rot = x_m * cos_o + y_m * sin_o
        y_rot = -x_m * sin_o + y_m * cos_o
        # Convert to degree offsets
        ring.append([
            center_lon + x_rot * deg_per_m_lon,
            center_lat + y_rot * deg_per_m_lat,
        ])

    # Close the ring
    ring.append(ring[0][:])
    return ring


class DisplacementLayer(BaseLayer):
    """Visualize displacement between origin and reported/displaced positions.

    Renders arcs between origin and displaced positions, with optional
    scatter dots at both endpoints. Useful for showing where something
    *should be* versus where it *was reported*.

    Parameters
    ----------
    data
        Input data (DataFrame, list of dicts, etc.) with columns for
        both origin and displaced positions.
    origin
        Column names for the origin position, e.g. ``["lon", "lat"]``.
    displaced
        Column names for the displaced position, e.g. ``["rep_lon", "rep_lat"]``.
    show_arcs
        Whether to draw arcs between origin and displaced positions.
    show_origin_dots
        Whether to draw dots at origin positions.
    show_displaced_dots
        Whether to draw dots at displaced positions.
    arc_width
        Arc width accessor or constant.
    arc_source_color
        Color at the origin end of the arc (default green).
    arc_target_color
        Color at the displaced end of the arc (default red).
    great_circle
        Whether to draw great circle arcs.
    origin_color
        Fill color for origin dots (default green).
    origin_radius
        Radius for origin dots.
    origin_radius_min_pixels
        Minimum pixel radius for origin dots.
    displaced_color
        Fill color for displaced dots (default red).
    displaced_radius
        Radius for displaced dots.
    displaced_radius_min_pixels
        Minimum pixel radius for displaced dots.
    """

    LAYER_TYPE = "DisplacementLayer"

    def __init__(
        self,
        *,
        data: Any = None,
        origin: list[str] | None = None,
        displaced: list[str] | None = None,
        show_arcs: bool = True,
        show_origin_dots: bool = True,
        show_displaced_dots: bool = True,
        arc_width: Accessor = 1,
        arc_source_color: ColorAccessor = (76, 175, 80, 200),
        arc_target_color: ColorAccessor = (244, 67, 54, 200),
        great_circle: bool = False,
        origin_color: ColorAccessor = (76, 175, 80, 180),
        origin_radius: Accessor = 4,
        origin_radius_min_pixels: float = 3,
        displaced_color: ColorAccessor = (244, 67, 54, 180),
        displaced_radius: Accessor = 4,
        displaced_radius_min_pixels: float = 3,
        **kwargs: Any,
    ) -> None:
        self._origin = origin
        self._displaced = displaced
        self._show_arcs = show_arcs
        self._show_origin_dots = show_origin_dots
        self._show_displaced_dots = show_displaced_dots
        self._arc_width = arc_width
        self._arc_source_color = list(arc_source_color) if isinstance(arc_source_color, tuple) else arc_source_color
        self._arc_target_color = list(arc_target_color) if isinstance(arc_target_color, tuple) else arc_target_color
        self._great_circle = great_circle
        self._origin_color = list(origin_color) if isinstance(origin_color, tuple) else origin_color
        self._origin_radius = origin_radius
        self._origin_radius_min_pixels = origin_radius_min_pixels
        self._displaced_color = list(displaced_color) if isinstance(displaced_color, tuple) else displaced_color
        self._displaced_radius = displaced_radius
        self._displaced_radius_min_pixels = displaced_radius_min_pixels

        super().__init__(data=data, **kwargs)

    def to_specs(self) -> list[dict]:
        """Decompose into ArcLayer + ScatterplotLayer specs."""
        specs: list[dict] = []

        if self._show_arcs:
            arc = ArcLayer(
                data=self.data,
                id=f"{self.id}-arcs",
                get_source_position=self._origin,
                get_target_position=self._displaced,
                get_source_color=self._arc_source_color,
                get_target_color=self._arc_target_color,
                get_width=self._arc_width,
                great_circle=self._great_circle,
                opacity=self.opacity,
                pickable=self.pickable,
                auto_highlight=self.auto_highlight,
                visible=self.visible,
                min_zoom=self.min_zoom,
                max_zoom=self.max_zoom,
            )
            specs.append(arc.to_spec())

        if self._show_origin_dots:
            origin_scatter = ScatterplotLayer(
                data=self.data,
                id=f"{self.id}-origin",
                get_position=self._origin,
                get_fill_color=self._origin_color,
                get_radius=self._origin_radius,
                radius_min_pixels=self._origin_radius_min_pixels,
                opacity=self.opacity,
                pickable=self.pickable,
                visible=self.visible,
                min_zoom=self.min_zoom,
                max_zoom=self.max_zoom,
            )
            specs.append(origin_scatter.to_spec())

        if self._show_displaced_dots:
            displaced_scatter = ScatterplotLayer(
                data=self.data,
                id=f"{self.id}-displaced",
                get_position=self._displaced,
                get_fill_color=self._displaced_color,
                get_radius=self._displaced_radius,
                radius_min_pixels=self._displaced_radius_min_pixels,
                opacity=self.opacity,
                pickable=self.pickable,
                visible=self.visible,
                min_zoom=self.min_zoom,
                max_zoom=self.max_zoom,
            )
            specs.append(displaced_scatter.to_spec())

        return specs

    def to_spec(self) -> dict:
        """Return the primary (arc) spec as a fallback."""
        specs = self.to_specs()
        return specs[0] if specs else {}


class EllipseLayer(BaseLayer):
    """Render ellipses or circles from center coordinates and axis dimensions.

    Each row in the data produces an ellipse (or circle) polygon plus an
    optional center-point dot.  Axis lengths can be given as diameters
    (default) or radii (``is_semi=True``), in meters, kilometers, or
    nautical miles.

    Parameters
    ----------
    data
        Input data (DataFrame, list of dicts, etc.) with columns for
        center coordinates and axis dimensions.
    center
        Column names for the center position, e.g. ``["lon", "lat"]``.
    major_axis
        Column name or constant value for the major axis length.
    minor_axis
        Column name or constant for the minor axis length.
        If ``None``, defaults to ``major_axis`` (circle).
    orientation
        Column name or constant for the rotation angle.
        0 = major axis points north, values increase clockwise.
    is_semi
        If ``True`` axis values are radii; if ``False`` (default) they
        are diameters.
    orientation_units
        ``"degrees"`` (default) or ``"radians"``.
    units
        Length unit for axis values: ``"meters"`` (default),
        ``"kilometers"``, or ``"nautical_miles"``.
    num_vertices
        Number of vertices for the polygon approximation.
    show_center_dots
        Whether to render dots at ellipse centers.
    fill_color
        Fill color for the ellipse polygons.
    line_color
        Outline color for the ellipse polygons.
    line_width
        Outline width for the ellipse polygons.
    filled
        Whether to fill the ellipse polygons.
    stroked
        Whether to stroke the ellipse outlines.
    center_dot_color
        Fill color for center dots.
    center_dot_radius
        Radius accessor or constant for center dots.
    center_dot_radius_min_pixels
        Minimum pixel radius for center dots.
    """

    LAYER_TYPE = "EllipseLayer"

    def __init__(
        self,
        *,
        data: Any = None,
        center: list[str] | None = None,
        major_axis: str | float | None = None,
        minor_axis: str | float | None = None,
        orientation: str | float = 0.0,
        is_semi: bool = False,
        orientation_units: str = "degrees",
        units: str = "meters",
        num_vertices: int = 64,
        show_center_dots: bool = False,
        fill_color: ColorAccessor = (0, 140, 255, 100),
        line_color: ColorAccessor = (0, 100, 200, 255),
        line_width: Accessor = 1,
        filled: bool = True,
        stroked: bool = True,
        center_dot_color: ColorAccessor = (255, 255, 255, 255),
        center_dot_radius: Accessor = 100,
        center_dot_radius_min_pixels: float = 4,
        **kwargs: Any,
    ) -> None:
        if orientation_units not in ("degrees", "radians"):
            msg = f"orientation_units must be 'degrees' or 'radians', got {orientation_units!r}"
            raise ValueError(msg)
        if units not in _UNIT_TO_METERS:
            msg = f"units must be one of {sorted(_UNIT_TO_METERS)}, got {units!r}"
            raise ValueError(msg)
        if num_vertices < 3:
            msg = f"num_vertices must be >= 3, got {num_vertices}"
            raise ValueError(msg)

        self._center = center
        self._major_axis = major_axis
        self._minor_axis = minor_axis
        self._orientation = orientation
        self._is_semi = is_semi
        self._orientation_units = orientation_units
        self._units = units
        self._num_vertices = num_vertices
        self._show_center_dots = show_center_dots
        self._fill_color = list(fill_color) if isinstance(fill_color, tuple) else fill_color
        self._line_color = list(line_color) if isinstance(line_color, tuple) else line_color
        self._line_width = line_width
        self._filled = filled
        self._stroked = stroked
        self._center_dot_color = list(center_dot_color) if isinstance(center_dot_color, tuple) else center_dot_color
        self._center_dot_radius = center_dot_radius
        self._center_dot_radius_min_pixels = center_dot_radius_min_pixels

        super().__init__(data=data, **kwargs)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _resolve(self, row: dict, accessor: str | float | None, fallback: float = 0.0) -> float:
        """Return a float from *accessor*: column lookup if str, else the value itself."""
        if accessor is None:
            return fallback
        if isinstance(accessor, str):
            return float(row[accessor])
        return float(accessor)

    # ------------------------------------------------------------------
    # spec generation
    # ------------------------------------------------------------------

    def to_specs(self) -> list[dict]:
        """Decompose into PolygonLayer (+ optional ScatterplotLayer) specs."""
        raw_data = prepare_data(self.data) if self.data is not None else []
        if not isinstance(raw_data, list):
            msg = "EllipseLayer requires tabular data (DataFrame or list of dicts)"
            raise TypeError(msg)
        if self._center is None:
            msg = "EllipseLayer requires center=[lon_col, lat_col]"
            raise TypeError(msg)

        unit_factor = _UNIT_TO_METERS[self._units]
        use_radians = self._orientation_units == "radians"

        augmented: list[dict] = []
        for row in raw_data:
            row = dict(row)  # shallow copy
            lon = row[self._center[0]]
            lat = row[self._center[1]]

            major = self._resolve(row, self._major_axis)
            minor = self._resolve(row, self._minor_axis, fallback=major)
            orient = self._resolve(row, self._orientation)

            # Convert to semi-axis in meters
            semi_major = major * unit_factor if self._is_semi else major * unit_factor / 2.0
            semi_minor = minor * unit_factor if self._is_semi else minor * unit_factor / 2.0

            # Convert to radians
            orient_rad = orient if use_radians else math.radians(orient)

            row["_ellipse_polygon"] = _compute_ellipse_ring(
                lon, lat, semi_major, semi_minor, orient_rad, self._num_vertices,
            )
            augmented.append(row)

        specs: list[dict] = []

        poly = PolygonLayer(
            data=augmented,
            id=f"{self.id}-rings",
            get_polygon="_ellipse_polygon",
            get_fill_color=self._fill_color,
            get_line_color=self._line_color,
            get_line_width=self._line_width,
            filled=self._filled,
            stroked=self._stroked,
            opacity=self.opacity,
            pickable=self.pickable,
            auto_highlight=self.auto_highlight,
            visible=self.visible,
            min_zoom=self.min_zoom,
            max_zoom=self.max_zoom,
        )
        specs.append(poly.to_spec())

        if self._show_center_dots:
            scatter = ScatterplotLayer(
                data=augmented,
                id=f"{self.id}-centers",
                get_position=self._center,
                get_fill_color=self._center_dot_color,
                get_radius=self._center_dot_radius,
                radius_min_pixels=self._center_dot_radius_min_pixels,
                opacity=self.opacity,
                pickable=self.pickable,
                visible=self.visible,
                min_zoom=self.min_zoom,
                max_zoom=self.max_zoom,
            )
            specs.append(scatter.to_spec())

        return specs

    def to_spec(self) -> dict:
        """Return the primary (polygon) spec as a fallback."""
        specs = self.to_specs()
        return specs[0] if specs else {}
