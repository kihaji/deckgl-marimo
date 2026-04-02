"""Composite deck.gl layers that decompose into multiple sub-layers."""

from __future__ import annotations

from typing import Any

from deckgl_marimo._base import BaseLayer
from deckgl_marimo.layers._core import ArcLayer, ScatterplotLayer


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
        arc_width: Any = 1,
        arc_source_color: Any = (76, 175, 80, 200),
        arc_target_color: Any = (244, 67, 54, 200),
        great_circle: bool = False,
        origin_color: Any = (76, 175, 80, 180),
        origin_radius: Any = 4,
        origin_radius_min_pixels: float = 3,
        displaced_color: Any = (244, 67, 54, 180),
        displaced_radius: Any = 4,
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
            )
            specs.append(displaced_scatter.to_spec())

        return specs

    def to_spec(self) -> dict:
        """Return the primary (arc) spec as a fallback."""
        specs = self.to_specs()
        return specs[0] if specs else {}
