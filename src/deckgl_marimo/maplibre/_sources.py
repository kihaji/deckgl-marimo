"""MapLibre source wrappers.

Ported from deckgl_dash's ``maplibre/sources.py``.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


class RasterSource:
    """MapLibre raster tile source.

    Used for XYZ tile servers, WMS, WMTS, or any raster tile endpoint —
    the primary building block for composing WMS base layers, which is
    this library's headline MapLibre use case.

    Examples
    --------
    XYZ tiles::

        RasterSource(tiles=["https://tile.openstreetmap.org/{z}/{x}/{y}.png"])

    WMS::

        RasterSource.from_wms(
            base_url="https://ows.terrestris.de/osm/service",
            layers="TOPO-WMS",
        )

    Parameters
    ----------
    tiles
        Tile URL templates with ``{z}``, ``{x}``, ``{y}`` placeholders.
    tile_size
        Tile size in pixels.
    min_zoom, max_zoom
        Zoom range at which tiles are requested.
    bounds
        Bounding box ``[west, south, east, north]`` in WGS84.
    attribution
        Attribution string for the source.
    scheme
        Tile scheme: ``"xyz"`` (default) or ``"tms"``.
    """

    def __init__(
        self,
        tiles: list[str] | None = None,
        tile_size: int = 256,
        min_zoom: int = 0,
        max_zoom: int = 22,
        bounds: list[float] | None = None,
        attribution: str | None = None,
        scheme: str = "xyz",
    ) -> None:
        self.tiles = tiles or []
        self.tile_size = tile_size
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom
        self.bounds = bounds
        self.attribution = attribution
        self.scheme = scheme

    @classmethod
    def from_wms(
        cls,
        base_url: str,
        layers: str,
        tile_size: int = 256,
        format: str = "image/png",
        transparent: bool = True,
        version: str = "1.1.1",
        crs: str = "EPSG:3857",
        styles: str = "",
        extra_params: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> RasterSource:
        """Create a raster source from a WMS endpoint.

        Builds a GetMap tile-URL template with MapLibre's
        ``{bbox-epsg-3857}`` placeholder.

        Parameters
        ----------
        base_url
            WMS service base URL (query parameters are merged if present).
        layers
            WMS layer name(s); comma-separate multiple layers.
        tile_size
            Tile size in pixels (also sent as WIDTH/HEIGHT).
        format
            Image format, e.g. ``"image/png"``.
        transparent
            Request a transparent background.
        version
            WMS version; 1.3.x switches SRS -> CRS automatically.
        crs
            Coordinate reference system (Web Mercator by default).
        styles
            WMS STYLES parameter.
        extra_params
            Additional WMS query parameters.
        **kwargs
            Forwarded to :class:`RasterSource` (bounds, attribution, ...).
        """
        params = {
            "SERVICE": "WMS",
            "VERSION": version,
            "REQUEST": "GetMap",
            "LAYERS": layers,
            "STYLES": styles,
            "FORMAT": format,
            "TRANSPARENT": "TRUE" if transparent else "FALSE",
            "WIDTH": str(tile_size),
            "HEIGHT": str(tile_size),
        }
        if version.startswith("1.3"):
            params["CRS"] = crs
        else:
            params["SRS"] = crs
        params["BBOX"] = "{bbox-epsg-3857}"

        if extra_params:
            params.update(extra_params)

        parsed = urlparse(base_url)
        for key, value in parse_qs(parsed.query).items():
            if key.upper() not in params:
                params[key.upper()] = value[0] if value else ""

        query_string = urlencode(params, safe="{}-")
        wms_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", query_string, ""))
        return cls(tiles=[wms_url], tile_size=tile_size, **kwargs)

    def to_dict(self) -> dict[str, Any]:
        """Convert to a MapLibre source spec dict."""
        result: dict[str, Any] = {"type": "raster", "tiles": self.tiles, "tileSize": self.tile_size}
        if self.min_zoom != 0:
            result["minzoom"] = self.min_zoom
        if self.max_zoom != 22:
            result["maxzoom"] = self.max_zoom
        if self.bounds:
            result["bounds"] = self.bounds
        if self.attribution:
            result["attribution"] = self.attribution
        if self.scheme != "xyz":
            result["scheme"] = self.scheme
        return result

    def __repr__(self) -> str:
        return f"RasterSource(tiles={self.tiles}, tile_size={self.tile_size})"


class VectorSource:
    """MapLibre vector tile source for PBF/MVT tiles.

    Examples
    --------
    ::

        VectorSource(tiles=["https://example.com/{z}/{x}/{y}.pbf"])
        VectorSource(url="https://example.com/tiles.json")   # TileJSON

    Parameters
    ----------
    tiles
        Tile URL templates (alternative to ``url``).
    url
        TileJSON URL (alternative to ``tiles``).
    min_zoom, max_zoom
        Zoom range at which tiles are requested.
    bounds
        Bounding box ``[west, south, east, north]`` in WGS84.
    attribution
        Attribution string.
    scheme
        ``"xyz"`` (default) or ``"tms"``.
    promote_id
        Property to use as feature ID — a string applied to all layers,
        or a dict mapping source-layer names to properties.
    """

    def __init__(
        self,
        tiles: list[str] | None = None,
        url: str | None = None,
        min_zoom: int = 0,
        max_zoom: int = 22,
        bounds: list[float] | None = None,
        attribution: str | None = None,
        scheme: str = "xyz",
        promote_id: str | dict[str, str] | None = None,
    ) -> None:
        self.tiles = tiles
        self.url = url
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom
        self.bounds = bounds
        self.attribution = attribution
        self.scheme = scheme
        self.promote_id = promote_id

    def to_dict(self) -> dict[str, Any]:
        """Convert to a MapLibre source spec dict."""
        result: dict[str, Any] = {"type": "vector"}
        if self.tiles:
            result["tiles"] = self.tiles
        if self.url:
            result["url"] = self.url
        if self.min_zoom != 0:
            result["minzoom"] = self.min_zoom
        if self.max_zoom != 22:
            result["maxzoom"] = self.max_zoom
        if self.bounds:
            result["bounds"] = self.bounds
        if self.attribution:
            result["attribution"] = self.attribution
        if self.scheme != "xyz":
            result["scheme"] = self.scheme
        if self.promote_id:
            result["promoteId"] = self.promote_id
        return result

    def __repr__(self) -> str:
        if self.url:
            return f"VectorSource(url={self.url!r})"
        return f"VectorSource(tiles={self.tiles})"


class GeoJSONSource:
    """MapLibre GeoJSON source for inline or remote GeoJSON data.

    Examples
    --------
    ::

        GeoJSONSource(data={"type": "FeatureCollection", "features": [...]})
        GeoJSONSource(data="https://example.com/data.geojson")

    Parameters
    ----------
    data
        GeoJSON dict or URL string.
    cluster
        Enable point clustering.
    cluster_radius
        Cluster radius in pixels.
    cluster_max_zoom
        Max zoom to cluster points.
    cluster_min_points
        Minimum points to form a cluster.
    cluster_properties
        Custom aggregation expressions for clusters.
    line_metrics
        Calculate line distance metrics (needed for line-gradient).
    tolerance
        Douglas-Peucker simplification tolerance.
    buffer
        Tile buffer size.
    max_zoom
        Maximum zoom level to generate tiles for.
    attribution
        Attribution string.
    promote_id
        Property to use as feature ID.
    generate_id
        Auto-generate feature IDs.
    """

    def __init__(
        self,
        data: str | dict[str, Any],
        cluster: bool = False,
        cluster_radius: int = 50,
        cluster_max_zoom: int | None = None,
        cluster_min_points: int = 2,
        cluster_properties: dict[str, Any] | None = None,
        line_metrics: bool = False,
        tolerance: float = 0.375,
        buffer: int = 128,
        max_zoom: int = 18,
        attribution: str | None = None,
        promote_id: str | None = None,
        generate_id: bool = False,
    ) -> None:
        self.data = data
        self.cluster = cluster
        self.cluster_radius = cluster_radius
        self.cluster_max_zoom = cluster_max_zoom
        self.cluster_min_points = cluster_min_points
        self.cluster_properties = cluster_properties
        self.line_metrics = line_metrics
        self.tolerance = tolerance
        self.buffer = buffer
        self.max_zoom = max_zoom
        self.attribution = attribution
        self.promote_id = promote_id
        self.generate_id = generate_id

    def to_dict(self) -> dict[str, Any]:
        """Convert to a MapLibre source spec dict."""
        result: dict[str, Any] = {"type": "geojson", "data": self.data}
        if self.cluster:
            result["cluster"] = True
            result["clusterRadius"] = self.cluster_radius
            if self.cluster_max_zoom is not None:
                result["clusterMaxZoom"] = self.cluster_max_zoom
            if self.cluster_min_points != 2:
                result["clusterMinPoints"] = self.cluster_min_points
            if self.cluster_properties:
                result["clusterProperties"] = self.cluster_properties
        if self.line_metrics:
            result["lineMetrics"] = True
        if self.tolerance != 0.375:
            result["tolerance"] = self.tolerance
        if self.buffer != 128:
            result["buffer"] = self.buffer
        if self.max_zoom != 18:
            result["maxzoom"] = self.max_zoom
        if self.attribution:
            result["attribution"] = self.attribution
        if self.promote_id:
            result["promoteId"] = self.promote_id
        if self.generate_id:
            result["generateId"] = True
        return result

    def __repr__(self) -> str:
        if isinstance(self.data, str):
            return f"GeoJSONSource(data={self.data!r})"
        return f"GeoJSONSource(data=<{len(self.data.get('features', []))} features>)"
