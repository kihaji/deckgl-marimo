"""Drawing/editing configuration for the Map widget.

Pairs with ``Map(drawing_config=...)`` and the ``drawing_features`` /
``drawing_event`` traitlets. The frontend renders an
``EditableGeoJsonLayer`` (@deck.gl-community/editable-layers) on top of
the regular deck.gl layers; drawn features arrive in Python as GeoJSON.

Ported from deckgl_dash's ``drawing.py``.
"""

from __future__ import annotations

from typing import Any

from deckgl_marimo._color_scale import _parse_color

DRAWING_MODES = {
    "draw_line", "draw_polygon", "draw_circle", "draw_rectangle",
    "draw_square", "draw_point", "view", "modify", "translate", "delete",
}

EMPTY_FEATURE_COLLECTION: dict[str, Any] = {"type": "FeatureCollection", "features": []}


def _normalize_color(value: Any) -> list[int]:
    """Normalize hex/named/RGB(A) colors to an RGBA list."""
    if isinstance(value, (list, tuple)):
        rgba = list(value)
    else:
        rgba = _parse_color(value)
    if len(rgba) == 3:
        rgba = [*rgba, 255]
    return [int(c) for c in rgba]


class DrawingStyle:
    """Style overrides for drawn features.

    Parameters
    ----------
    fill_color
        Fill color for completed features (hex, name, RGB, or RGBA).
    line_color
        Stroke color for completed features.
    line_width
        Stroke width in pixels.
    tentative_fill_color
        Fill color for features while being drawn.
    tentative_line_color
        Stroke color for features while being drawn.
    edit_handle_point_color
        Color of vertex edit handles in modify mode.
    point_radius
        Radius of drawn points in pixels.
    show_measurements
        Show distance/area tooltips while drawing lines and circles.
    """

    def __init__(
        self,
        *,
        fill_color: Any = None,
        line_color: Any = None,
        line_width: float | None = None,
        tentative_fill_color: Any = None,
        tentative_line_color: Any = None,
        edit_handle_point_color: Any = None,
        point_radius: float | None = None,
        show_measurements: bool | None = None,
    ) -> None:
        self._props: dict[str, Any] = {}
        for key, value, is_color in (
            ("fillColor", fill_color, True),
            ("lineColor", line_color, True),
            ("lineWidth", line_width, False),
            ("tentativeFillColor", tentative_fill_color, True),
            ("tentativeLineColor", tentative_line_color, True),
            ("editHandlePointColor", edit_handle_point_color, True),
            ("pointRadius", point_radius, False),
            ("showMeasurements", show_measurements, False),
        ):
            if value is not None:
                self._props[key] = _normalize_color(value) if is_color else value

    def to_dict(self) -> dict[str, Any]:
        return dict(self._props)


class DrawingConfig:
    """Configuration for the drawing/editing system.

    Parameters
    ----------
    mode
        One of ``'draw_line'``, ``'draw_polygon'``, ``'draw_circle'``,
        ``'draw_rectangle'``, ``'draw_square'``, ``'draw_point'``,
        ``'view'``, ``'modify'``, ``'translate'``, ``'delete'``.
        In ``'delete'`` mode each click on a feature deletes it.
    selected_feature_indexes
        Feature indexes selected for editing (``'modify'``/``'translate'``).
    style
        Optional :class:`DrawingStyle` overrides.
    delete_selected
        Set True to delete the currently selected feature(s); the
        frontend resets the flag after acting on it.

    Example
    -------
    ::

        m = dgl.Map(drawing_config=dgl.DrawingConfig(
            mode="draw_polygon",
            style=dgl.DrawingStyle(fill_color=[255, 140, 0, 100], line_width=2),
        ))
        drawn = widget.value.get("drawing_features", {})
    """

    def __init__(
        self,
        mode: str = "view",
        *,
        selected_feature_indexes: list[int] | None = None,
        style: DrawingStyle | None = None,
        delete_selected: bool = False,
    ) -> None:
        if mode not in DRAWING_MODES:
            raise ValueError(
                f"Invalid drawing mode {mode!r}. Must be one of: {sorted(DRAWING_MODES)}"
            )
        self.mode = mode
        self.selected_feature_indexes = selected_feature_indexes or []
        self.style = style
        self.delete_selected = delete_selected

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"mode": self.mode}
        if self.selected_feature_indexes:
            result["selectedFeatureIndexes"] = self.selected_feature_indexes
        if self.style:
            result["style"] = self.style.to_dict()
        if self.delete_selected:
            result["deleteSelected"] = True
        return result
