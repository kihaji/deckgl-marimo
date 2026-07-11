"""MapLibre configuration for composed basemaps.

Ported from deckgl_dash's ``maplibre/config.py``, adapted to reuse this
library's :class:`~deckgl_marimo.Basemaps` catalog for style aliases.
"""

from __future__ import annotations

from typing import Any

from deckgl_marimo._basemaps import Basemaps


def empty_style() -> dict[str, Any]:
    """An empty MapLibre style spec — for WMS-only / layers-only maps."""
    return {"version": 8, "sources": {}, "layers": []}


class MapLibreConfig:
    """Composed basemap configuration: a base style plus extra sources/layers.

    Pass to ``Map(basemap=config)``. The frontend loads the base style and
    then applies the additional sources and MapLibre layers on top —
    without hand-writing a full style JSON document.

    Examples
    --------
    WMS raster over a named basemap::

        from deckgl_marimo.maplibre import MapLibreConfig, RasterSource, RasterLayer

        config = MapLibreConfig(
            style="positron",
            sources={"wms": RasterSource.from_wms(
                "https://ows.terrestris.de/osm/service", layers="TOPO-WMS",
            )},
            map_layers=[RasterLayer(id="wms-topo", source="wms", raster_opacity=0.7)],
        )
        m = dgl.Map(basemap=config, layers=[...])

    Custom vector tiles::

        config = MapLibreConfig(
            style="dark-matter",
            sources={"custom": VectorSource(tiles=["https://example.com/{z}/{x}/{y}.pbf"])},
            map_layers=[FillLayer(id="custom-fill", source="custom", source_layer="buildings")],
        )

    Parameters
    ----------
    style
        Basemap alias (``"positron"``), MapLibre style URL, or inline style
        spec dict. Use :func:`empty_style` for WMS-only maps.
    sources
        Extra sources keyed by source id — values may be Source objects
        (:class:`RasterSource`, :class:`VectorSource`,
        :class:`GeoJSONSource`) or raw spec dicts.
    map_layers
        Extra MapLibre style layers — Layer objects
        (:class:`RasterLayer`, :class:`FillLayer`, ...) or raw spec dicts.
        Applied in order after the base style loads.
    map_options
        Additional options merged into the MapLibre ``Map`` constructor.
    """

    def __init__(
        self,
        style: str | dict[str, Any] = "dark-matter",
        sources: dict[str, Any] | None = None,
        map_layers: list[Any] | None = None,
        map_options: dict[str, Any] | None = None,
    ) -> None:
        self.style = style
        self.sources = sources or {}
        self.map_layers = map_layers or []
        self.map_options = map_options or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to the dict shape the widget's ``maplibre_config`` traitlet carries."""
        style = self.style
        if isinstance(style, str):
            style = Basemaps.resolve(style)

        sources = {
            source_id: spec.to_dict() if hasattr(spec, "to_dict") else spec
            for source_id, spec in self.sources.items()
        }
        layers = [
            spec.to_dict() if hasattr(spec, "to_dict") else spec
            for spec in self.map_layers
        ]

        result: dict[str, Any] = {"style": style}
        if sources:
            result["sources"] = sources
        if layers:
            result["mapLayers"] = layers
        if self.map_options:
            result["mapOptions"] = self.map_options
        return result

    def __repr__(self) -> str:
        style_repr = self.style if isinstance(self.style, str) else "<inline style>"
        return (
            f"MapLibreConfig(style={style_repr!r}, sources={len(self.sources)}, "
            f"map_layers={len(self.map_layers)})"
        )
