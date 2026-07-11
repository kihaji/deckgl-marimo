"""MapLibre style-layer wrappers.

These are MapLibre GL JS style layers, NOT deck.gl layers — use them for
styling raster/vector/GeoJSON sources rendered by the basemap engine
underneath the deck.gl overlay.

Ported from deckgl_dash's ``maplibre/layers.py``. Convenience kwargs are
snake_case and map onto MapLibre's kebab-case paint/layout properties;
anything not covered can be passed via the ``paint=`` / ``layout=`` dicts.
"""

from __future__ import annotations

from typing import Any

# MapLibre expression, e.g. ["get", "height"]
Expression = list[Any]
# Static value or expression
PropertyValue = Any


def _set_kebab(target: dict[str, Any], values: dict[str, Any]) -> None:
    """Copy non-None convenience kwargs into a paint/layout dict, kebab-cased."""
    for key, value in values.items():
        if value is not None:
            target[key.replace("_", "-")] = value


class BaseMapLibreLayer:
    """Base class for MapLibre style layers.

    Parameters
    ----------
    id
        Unique layer ID within the style.
    source
        Source ID this layer draws from.
    source_layer
        Source layer name (required for vector tile sources).
    min_zoom, max_zoom
        Zoom range for layer visibility (MapLibre ``minzoom``/``maxzoom``).
    filter
        MapLibre filter expression.
    layout
        Raw layout properties (kebab-case keys) merged after convenience kwargs.
    paint
        Raw paint properties (kebab-case keys) merged after convenience kwargs.
    metadata
        Arbitrary metadata dict.
    """

    _layer_type: str = ""

    def __init__(
        self,
        id: str,
        source: str,
        source_layer: str | None = None,
        min_zoom: float | None = None,
        max_zoom: float | None = None,
        filter: Expression | None = None,
        layout: dict[str, PropertyValue] | None = None,
        paint: dict[str, PropertyValue] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.id = id
        self.source = source
        self.source_layer = source_layer
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom
        self.filter = filter
        self.layout = dict(layout or {})
        self.paint = dict(paint or {})
        self.metadata = metadata

    def to_dict(self) -> dict[str, Any]:
        """Convert to a MapLibre layer spec dict."""
        result: dict[str, Any] = {"id": self.id, "type": self._layer_type, "source": self.source}
        if self.source_layer:
            result["source-layer"] = self.source_layer
        if self.min_zoom is not None:
            result["minzoom"] = self.min_zoom
        if self.max_zoom is not None:
            result["maxzoom"] = self.max_zoom
        if self.filter:
            result["filter"] = self.filter
        if self.layout:
            result["layout"] = self.layout
        if self.paint:
            result["paint"] = self.paint
        if self.metadata:
            result["metadata"] = self.metadata
        return result

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id!r}, source={self.source!r})"


class FillLayer(BaseMapLibreLayer):
    """MapLibre fill layer — filled polygons.

    Example
    -------
    ::

        FillLayer(
            id="buildings", source="vector-tiles", source_layer="building",
            fill_color="#ff0000", fill_opacity=0.5,
        )
    """

    _layer_type = "fill"

    def __init__(
        self,
        id: str,
        source: str,
        source_layer: str | None = None,
        fill_color: PropertyValue | None = None,
        fill_opacity: PropertyValue | None = None,
        fill_outline_color: PropertyValue | None = None,
        fill_pattern: PropertyValue | None = None,
        fill_antialias: bool | None = None,
        fill_translate: list[float] | None = None,
        fill_translate_anchor: str | None = None,
        visibility: str | None = None,
        fill_sort_key: PropertyValue | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(id, source, source_layer, **kwargs)
        _set_kebab(self.paint, {
            "fill_color": fill_color,
            "fill_opacity": fill_opacity,
            "fill_outline_color": fill_outline_color,
            "fill_pattern": fill_pattern,
            "fill_antialias": fill_antialias,
            "fill_translate": fill_translate,
            "fill_translate_anchor": fill_translate_anchor,
        })
        _set_kebab(self.layout, {
            "visibility": visibility,
            "fill_sort_key": fill_sort_key,
        })


class LineLayer(BaseMapLibreLayer):
    """MapLibre line layer — lines and polygon outlines.

    Example
    -------
    ::

        LineLayer(
            id="roads", source="vector-tiles", source_layer="road",
            line_color="#000000", line_width=2,
        )
    """

    _layer_type = "line"

    def __init__(
        self,
        id: str,
        source: str,
        source_layer: str | None = None,
        line_color: PropertyValue | None = None,
        line_width: PropertyValue | None = None,
        line_opacity: PropertyValue | None = None,
        line_blur: PropertyValue | None = None,
        line_dasharray: list[float] | None = None,
        line_gap_width: PropertyValue | None = None,
        line_offset: PropertyValue | None = None,
        line_pattern: PropertyValue | None = None,
        line_translate: list[float] | None = None,
        line_translate_anchor: str | None = None,
        line_gradient: Expression | None = None,
        visibility: str | None = None,
        line_cap: str | None = None,
        line_join: str | None = None,
        line_miter_limit: float | None = None,
        line_round_limit: float | None = None,
        line_sort_key: PropertyValue | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(id, source, source_layer, **kwargs)
        _set_kebab(self.paint, {
            "line_color": line_color,
            "line_width": line_width,
            "line_opacity": line_opacity,
            "line_blur": line_blur,
            "line_dasharray": line_dasharray,
            "line_gap_width": line_gap_width,
            "line_offset": line_offset,
            "line_pattern": line_pattern,
            "line_translate": line_translate,
            "line_translate_anchor": line_translate_anchor,
            "line_gradient": line_gradient,
        })
        _set_kebab(self.layout, {
            "visibility": visibility,
            "line_cap": line_cap,
            "line_join": line_join,
            "line_miter_limit": line_miter_limit,
            "line_round_limit": line_round_limit,
            "line_sort_key": line_sort_key,
        })


class RasterLayer(BaseMapLibreLayer):
    """MapLibre raster layer — renders a raster (XYZ/WMS) source.

    Example
    -------
    ::

        RasterLayer(id="wms-topo", source="wms", raster_opacity=0.8)
    """

    _layer_type = "raster"

    def __init__(
        self,
        id: str,
        source: str,
        raster_opacity: float | None = None,
        raster_hue_rotate: float | None = None,
        raster_brightness_min: float | None = None,
        raster_brightness_max: float | None = None,
        raster_saturation: float | None = None,
        raster_contrast: float | None = None,
        raster_resampling: str | None = None,
        raster_fade_duration: float | None = None,
        visibility: str | None = None,
        **kwargs: Any,
    ) -> None:
        # Raster layers don't use source_layer
        super().__init__(id, source, source_layer=None, **kwargs)
        _set_kebab(self.paint, {
            "raster_opacity": raster_opacity,
            "raster_hue_rotate": raster_hue_rotate,
            "raster_brightness_min": raster_brightness_min,
            "raster_brightness_max": raster_brightness_max,
            "raster_saturation": raster_saturation,
            "raster_contrast": raster_contrast,
            "raster_resampling": raster_resampling,
            "raster_fade_duration": raster_fade_duration,
        })
        _set_kebab(self.layout, {"visibility": visibility})


class CircleLayer(BaseMapLibreLayer):
    """MapLibre circle layer — points as circles.

    Example
    -------
    ::

        CircleLayer(
            id="points", source="geojson-points",
            circle_radius=6, circle_color="#007cbf",
        )
    """

    _layer_type = "circle"

    def __init__(
        self,
        id: str,
        source: str,
        source_layer: str | None = None,
        circle_radius: PropertyValue | None = None,
        circle_color: PropertyValue | None = None,
        circle_blur: PropertyValue | None = None,
        circle_opacity: PropertyValue | None = None,
        circle_stroke_width: PropertyValue | None = None,
        circle_stroke_color: PropertyValue | None = None,
        circle_stroke_opacity: PropertyValue | None = None,
        circle_translate: list[float] | None = None,
        circle_translate_anchor: str | None = None,
        circle_pitch_scale: str | None = None,
        circle_pitch_alignment: str | None = None,
        visibility: str | None = None,
        circle_sort_key: PropertyValue | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(id, source, source_layer, **kwargs)
        _set_kebab(self.paint, {
            "circle_radius": circle_radius,
            "circle_color": circle_color,
            "circle_blur": circle_blur,
            "circle_opacity": circle_opacity,
            "circle_stroke_width": circle_stroke_width,
            "circle_stroke_color": circle_stroke_color,
            "circle_stroke_opacity": circle_stroke_opacity,
            "circle_translate": circle_translate,
            "circle_translate_anchor": circle_translate_anchor,
            "circle_pitch_scale": circle_pitch_scale,
            "circle_pitch_alignment": circle_pitch_alignment,
        })
        _set_kebab(self.layout, {
            "visibility": visibility,
            "circle_sort_key": circle_sort_key,
        })


class SymbolLayer(BaseMapLibreLayer):
    """MapLibre symbol layer — text labels and icons.

    Example
    -------
    ::

        SymbolLayer(
            id="labels", source="places",
            text_field=["get", "name"], text_size=12, text_color="#000000",
        )
    """

    _layer_type = "symbol"

    def __init__(
        self,
        id: str,
        source: str,
        source_layer: str | None = None,
        # layout (symbols style mostly via layout)
        text_field: PropertyValue | None = None,
        text_size: PropertyValue | None = None,
        text_font: list[str] | None = None,
        text_anchor: str | None = None,
        text_offset: list[float] | None = None,
        text_max_width: PropertyValue | None = None,
        text_justify: str | None = None,
        text_rotation_alignment: str | None = None,
        text_pitch_alignment: str | None = None,
        text_transform: str | None = None,
        text_letter_spacing: PropertyValue | None = None,
        text_line_height: PropertyValue | None = None,
        icon_image: PropertyValue | None = None,
        icon_size: PropertyValue | None = None,
        icon_anchor: str | None = None,
        icon_offset: list[float] | None = None,
        icon_rotation_alignment: str | None = None,
        icon_pitch_alignment: str | None = None,
        symbol_placement: str | None = None,
        symbol_spacing: float | None = None,
        symbol_sort_key: PropertyValue | None = None,
        visibility: str | None = None,
        # paint
        text_color: PropertyValue | None = None,
        text_opacity: PropertyValue | None = None,
        text_halo_color: PropertyValue | None = None,
        text_halo_width: PropertyValue | None = None,
        text_halo_blur: PropertyValue | None = None,
        icon_color: PropertyValue | None = None,
        icon_opacity: PropertyValue | None = None,
        icon_halo_color: PropertyValue | None = None,
        icon_halo_width: PropertyValue | None = None,
        icon_halo_blur: PropertyValue | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(id, source, source_layer, **kwargs)
        _set_kebab(self.layout, {
            "text_field": text_field,
            "text_size": text_size,
            "text_font": text_font,
            "text_anchor": text_anchor,
            "text_offset": text_offset,
            "text_max_width": text_max_width,
            "text_justify": text_justify,
            "text_rotation_alignment": text_rotation_alignment,
            "text_pitch_alignment": text_pitch_alignment,
            "text_transform": text_transform,
            "text_letter_spacing": text_letter_spacing,
            "text_line_height": text_line_height,
            "icon_image": icon_image,
            "icon_size": icon_size,
            "icon_anchor": icon_anchor,
            "icon_offset": icon_offset,
            "icon_rotation_alignment": icon_rotation_alignment,
            "icon_pitch_alignment": icon_pitch_alignment,
            "symbol_placement": symbol_placement,
            "symbol_spacing": symbol_spacing,
            "symbol_sort_key": symbol_sort_key,
            "visibility": visibility,
        })
        _set_kebab(self.paint, {
            "text_color": text_color,
            "text_opacity": text_opacity,
            "text_halo_color": text_halo_color,
            "text_halo_width": text_halo_width,
            "text_halo_blur": text_halo_blur,
            "icon_color": icon_color,
            "icon_opacity": icon_opacity,
            "icon_halo_color": icon_halo_color,
            "icon_halo_width": icon_halo_width,
            "icon_halo_blur": icon_halo_blur,
        })


class FillExtrusionLayer(BaseMapLibreLayer):
    """MapLibre fill-extrusion layer — 3D extruded polygons.

    Example
    -------
    ::

        FillExtrusionLayer(
            id="buildings-3d", source="vector-tiles", source_layer="building",
            fill_extrusion_color="#aaa",
            fill_extrusion_height=["get", "height"],
            fill_extrusion_opacity=0.6,
        )
    """

    _layer_type = "fill-extrusion"

    def __init__(
        self,
        id: str,
        source: str,
        source_layer: str | None = None,
        fill_extrusion_color: PropertyValue | None = None,
        fill_extrusion_opacity: float | None = None,
        fill_extrusion_height: PropertyValue | None = None,
        fill_extrusion_base: PropertyValue | None = None,
        fill_extrusion_pattern: PropertyValue | None = None,
        fill_extrusion_translate: list[float] | None = None,
        fill_extrusion_translate_anchor: str | None = None,
        fill_extrusion_vertical_gradient: bool | None = None,
        visibility: str | None = None,
        fill_extrusion_edge_radius: float | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(id, source, source_layer, **kwargs)
        _set_kebab(self.paint, {
            "fill_extrusion_color": fill_extrusion_color,
            "fill_extrusion_opacity": fill_extrusion_opacity,
            "fill_extrusion_height": fill_extrusion_height,
            "fill_extrusion_base": fill_extrusion_base,
            "fill_extrusion_pattern": fill_extrusion_pattern,
            "fill_extrusion_translate": fill_extrusion_translate,
            "fill_extrusion_translate_anchor": fill_extrusion_translate_anchor,
            "fill_extrusion_vertical_gradient": fill_extrusion_vertical_gradient,
        })
        _set_kebab(self.layout, {
            "visibility": visibility,
            "fill_extrusion_edge_radius": fill_extrusion_edge_radius,
        })
