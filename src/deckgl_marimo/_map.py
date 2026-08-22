"""Map widget for deckgl-marimo."""

from __future__ import annotations

import pathlib
from typing import TYPE_CHECKING, Any, ClassVar

import anywidget
import traitlets

from deckgl_marimo._base import BaseLayer, _raise_for_unknown_props
from deckgl_marimo._basemaps import Basemaps
from deckgl_marimo._data import materialize_rows

if TYPE_CHECKING:
    from deckgl_marimo.maplibre import MapLibreConfig

_STATIC = pathlib.Path(__file__).parent / "static"


class Map(anywidget.AnyWidget):
    """Interactive map widget with deck.gl layers on a MapLibre GL basemap.

    This is the single anywidget that renders all layers. Layers are
    plain Python objects (subclasses of :class:`BaseLayer`) that get
    serialized to JSON specs for the JavaScript frontend.

    Parameters
    ----------
    layers
        List of :class:`BaseLayer` instances to render.
    basemap
        Basemap style. Accepts a :class:`Basemaps` alias like
        ``"dark-matter"``, a full MapLibre style URL, an inline MapLibre
        style spec dict, or a
        :class:`~deckgl_marimo.maplibre.MapLibreConfig` composing a base
        style with extra sources (WMS/XYZ/vector/GeoJSON) and MapLibre
        layers.
    center
        Initial map center as ``(longitude, latitude)``.
    zoom
        Initial zoom level (0-22).
    pitch
        Initial pitch/tilt angle in degrees (0-85).
    bearing
        Initial rotation angle in degrees.
    height
        CSS height of the map container.
    width
        CSS width of the map container.
    show_perf_metrics
        Enable the FPS/frame-time tracker, which pushes ``perf_metrics``
        updates every 500 ms while the widget is displayed. Off by
        default to avoid constant traitlet traffic; can be toggled at
        runtime (``m.show_perf_metrics = True``).

    Examples
    --------
    >>> import deckgl_marimo as dgl
    >>> m = dgl.Map(
    ...     layers=[dgl.ScatterplotLayer(data=df, get_position=["lon", "lat"])],
    ...     basemap="dark-matter",
    ...     center=(-122.4, 37.8),
    ...     zoom=10,
    ... )
    """

    _esm = _STATIC / "deckgl-marimo.bundle.js"
    _css = _STATIC / "deckgl-marimo.bundle.css"

    # User-facing init kwargs — validated against to catch typos like
    # ``Map(layer=...)`` instead of ``Map(layers=...)``. Hand-listed
    # because Map has a single user-facing class; no MRO walking needed.
    _VALID_KWARGS: ClassVar[frozenset[str]] = frozenset({
        "layers", "basemap", "center", "zoom", "pitch", "bearing",
        "height", "width", "show_perf_metrics", "time_filter",
        "drawing_config", "drawing_features",
    })

    # Layer specifications (list of dicts from BaseLayer.to_spec())
    layer_specs = traitlets.List([]).tag(sync=True)

    # View state
    longitude = traitlets.Float(0.0).tag(sync=True)
    latitude = traitlets.Float(0.0).tag(sync=True)
    zoom = traitlets.Float(1.0).tag(sync=True)
    pitch = traitlets.Float(0.0).tag(sync=True)
    bearing = traitlets.Float(0.0).tag(sync=True)

    # Basemap
    basemap_style = traitlets.Unicode("").tag(sync=True)

    # Composed basemap configuration (maplibre.MapLibreConfig.to_dict()):
    # {style, sources, mapLayers, mapOptions}. When non-empty, its style
    # wins over basemap_style and the extra sources/layers are applied
    # after every style load.
    maplibre_config = traitlets.Dict({}).tag(sync=True)

    # Layout
    height = traitlets.Unicode("600px").tag(sync=True)
    width = traitlets.Unicode("100%").tag(sync=True)

    # Binary data transfer (bypasses JSON serialization)
    binary_data = traitlets.Bytes(b"").tag(sync=True)
    binary_metadata = traitlets.Dict({}).tag(sync=True)

    # Opt-in FPS/frame-time tracking. Off by default: the tracker runs a
    # requestAnimationFrame loop that pushes perf_metrics over the wire
    # every 500 ms — constant traitlet churn an idle map shouldn't pay.
    show_perf_metrics = traitlets.Bool(False).tag(sync=True)

    # Drawing/editing (see deckgl_marimo.DrawingConfig): the config drives an
    # EditableGeoJsonLayer in the frontend; drawn features sync back as
    # GeoJSON and drawing_event reports edit types.
    drawing_config = traitlets.Dict({}).tag(sync=True)
    drawing_features = traitlets.Dict({"type": "FeatureCollection", "features": []}).tag(sync=True)
    drawing_event = traitlets.Dict({}).tag(sync=True)

    # GPU time-filter animation (see deckgl_marimo.build_time_filter):
    # {domain, window, current, playing, speed, loop, softEdge?, layerIds?}.
    # Playback runs client-side; current_time reports the throttled head.
    time_filter = traitlets.Dict({}).tag(sync=True)
    current_time = traitlets.Float(0.0).tag(sync=True)

    # One-shot fit-bounds request applied by the JS side via map.fitBounds.
    # Carries a sequence number so repeated calls with identical bounds
    # still fire a change event.
    fit_bounds_request = traitlets.Dict({}).tag(sync=True)

    # Read-back from JS (JS -> Python). ``viewport`` carries longitude,
    # latitude, zoom, pitch, bearing and ``bounds`` ([[west, south], [east,
    # north]]); see the ``bounds`` property. Populated on map load and after
    # every camera move.
    viewport = traitlets.Dict({}).tag(sync=True)
    click_info = traitlets.Dict({}).tag(sync=True)
    hover_info = traitlets.Dict({}).tag(sync=True)
    perf_metrics = traitlets.Dict({}).tag(sync=True)

    def __init__(
        self,
        layers: list[BaseLayer] | None = None,
        *,
        basemap: str | dict[str, Any] | MapLibreConfig = "dark-matter",
        center: tuple[float, float] | None = None,
        zoom: float = 1.0,
        pitch: float = 0.0,
        bearing: float = 0.0,
        height: str = "600px",
        width: str = "100%",
        show_perf_metrics: bool = False,
        time_filter: dict[str, Any] | None = None,
        drawing_config: Any = None,
        _unsafe_props: bool = False,
        **kwargs: Any,
    ) -> None:
        if not _unsafe_props:
            _raise_for_unknown_props(type(self).__name__, kwargs, self._VALID_KWARGS)
        self._layers: list[BaseLayer] = list(layers or [])
        self._resolving_pick = False
        self._fit_bounds_seq = 0
        # Materialized-row cache for pick resolution, keyed by layer id.
        # Without it every click/hover re-converts the layer's full dataset.
        self._pick_rows_cache: dict[str, list | None] = {}
        specs = [spec for layer in self._layers for spec in layer.to_specs()]

        # basemap accepts: alias/URL string, a maplibre.MapLibreConfig, a
        # config dict ({"style": ...}), or an inline MapLibre style spec.
        style = ""
        ml_config: dict[str, Any] = {}
        if isinstance(basemap, str):
            style = Basemaps.resolve(basemap)
        elif isinstance(basemap, dict):
            # A config dict ({"style": ...}) or an inline MapLibre style spec
            ml_config = basemap if "style" in basemap else {"style": basemap}
        else:
            # MapLibreConfig (anything exposing to_dict)
            ml_config = basemap.to_dict()

        # Pre-pack binary data for layers that use binary mode
        bin_meta, bin_data = self._pack_binary(self._layers)

        init_kwargs: dict[str, Any] = {
            "layer_specs": specs,
            "basemap_style": style,
            "maplibre_config": ml_config,
            "binary_data": bin_data,
            "binary_metadata": bin_meta,
            "zoom": zoom,
            "pitch": pitch,
            "bearing": bearing,
            "height": height,
            "width": width,
            "show_perf_metrics": show_perf_metrics,
            "time_filter": time_filter or {},
            **kwargs,
        }
        if drawing_config is not None:
            init_kwargs["drawing_config"] = (
                drawing_config.to_dict() if hasattr(drawing_config, "to_dict") else drawing_config
            )

        if center is not None:
            init_kwargs["longitude"] = center[0]
            init_kwargs["latitude"] = center[1]

        super().__init__(**init_kwargs)

    @staticmethod
    def _pack_binary(layers: list[BaseLayer]) -> tuple[dict, bytes]:
        """Pack binary data for all layers. Returns (metadata, buffer)."""
        layer_metas = []
        buffers: list[bytes] = []
        offset = 0

        for layer in layers:
            result = layer.to_binary()
            if result is None:
                continue
            meta, buf = result
            # startIndices is only present for variable-length layers
            # (Polygon, Path, Trips) — fixed-size layers omit it.
            if "startIndices" in meta:
                meta["startIndices"]["offset"] += offset
            for attr_meta in meta["attributes"].values():
                attr_meta["offset"] += offset

            # Binary mode strips per-row data; deck.gl's default hover tooltip
            # reads object.tooltip, which is unreachable. Pre-pack tooltip
            # strings indexed by feature so the JS side can render them.
            rows = materialize_rows(layer.data)
            if rows and "tooltip" in rows[0]:
                meta["tooltips"] = [str(r.get("tooltip", "")) for r in rows]

            layer_metas.append(meta)
            buffers.append(buf)
            offset += len(buf)

        if layer_metas:
            return {"layers": layer_metas}, b"".join(buffers)
        return {}, b""

    @traitlets.observe("click_info", "hover_info")
    def _resolve_pick_object(self, change: Any) -> None:
        """Populate ``object`` on pick events for binary-packed layers.

        JS sends ``object: null`` when deck.gl has no iterable data to look
        up into (binary mode). We find the picked layer by id, materialize
        its source data, and fill in the row at ``index`` so downstream
        code can treat binary and JSON layers uniformly.
        """
        if self._resolving_pick:
            return
        info = change["new"] or {}
        if info.get("object") is not None:
            return
        layer_id = info.get("layer_id")
        index = info.get("index")
        if layer_id is None or index is None or index < 0:
            return
        layer = next((lyr for lyr in self._layers if lyr.id == layer_id), None)
        if layer is None:
            return
        if layer_id not in self._pick_rows_cache:
            self._pick_rows_cache[layer_id] = materialize_rows(layer.data)
        rows = self._pick_rows_cache[layer_id]
        if rows is None or index >= len(rows):
            return
        self._resolving_pick = True
        try:
            setattr(self, change["name"], {**info, "object": rows[index]})
        finally:
            self._resolving_pick = False

    def set_layers(self, layers: list[BaseLayer]) -> None:
        """Replace all layers on the map.

        This is the recommended way to update layers reactively (e.g. in a
        marimo cell that depends on slider values): it re-serializes the
        layer specs *and* re-packs binary buffers in one call, unlike
        assigning ``layer_specs`` directly, which silently skips binary
        packing.

        Parameters
        ----------
        layers
            The new list of :class:`BaseLayer` instances. Replaces any
            existing layers.
        """
        self._layers = list(layers)
        self._sync_layers()

    def add_layer(self, layer: BaseLayer) -> None:
        """Add a layer to the map.

        Parameters
        ----------
        layer
            A :class:`BaseLayer` subclass instance.
        """
        self._layers.append(layer)
        self._sync_layers()

    def remove_layer(self, layer_id: str) -> None:
        """Remove a layer by its ID.

        Parameters
        ----------
        layer_id
            The ``id`` of the layer to remove.
        """
        self._layers = [lyr for lyr in self._layers if lyr.id != layer_id]
        self._sync_layers()

    def update_layer(self, layer_id: str, **props: Any) -> None:
        """Update properties of an existing layer.

        Parameters
        ----------
        layer_id
            The ``id`` of the layer to update.
        **props
            Properties to update (snake_case). Validated against the
            layer's declared props; unknown keys raise ``TypeError`` with
            a "did you mean" suggestion.
        """
        layer = next((lyr for lyr in self._layers if lyr.id == layer_id), None)
        if layer is None:
            return

        # Explicit routing — never getattr/hasattr on the layer, whose
        # __getattr__ delegates to a lazily-created backing Map (a hasattr
        # probe would instantiate a hidden widget and mis-route keys that
        # happen to collide with Map traitlets, e.g. `zoom`).
        map_keys = [k for k in props if k in layer._MAP_KEYS]
        if map_keys:
            raise ValueError(
                f"{map_keys!r} are map-level settings for standalone layer "
                "display and cannot be changed via update_layer(); set them "
                "on the Map itself (e.g. map.zoom = 10)."
            )
        valid = layer._FIELD_KEYS | (layer._VALID_PROPS or frozenset())
        _raise_for_unknown_props(type(layer).__name__, props, valid)

        for key, value in props.items():
            if key in layer._FIELD_KEYS:
                setattr(layer, key, value)
            else:
                layer._props[key] = value
        self._sync_layers()

    def fit_bounds(self, bounds: list[list[float]], *, padding: int = 20) -> None:
        """Fit the viewport to the given bounds.

        The JS side applies an exact ``map.fitBounds(bounds, {padding})``.
        The Python-side view traitlets are also set to the bounds center
        and an approximate zoom so state is sane before/without a
        rendered frontend.

        Use :func:`deckgl_marimo.compute_bounds` to derive bounds from
        layer data.

        Parameters
        ----------
        bounds
            [[west, south], [east, north]] in degrees.
        padding
            Pixel padding around the bounds (applied by the JS side).
        """
        import math

        sw, ne = bounds
        self.longitude = (sw[0] + ne[0]) / 2
        self.latitude = (sw[1] + ne[1]) / 2

        # Approximate zoom: fit the larger angular span into a 360°-at-z0
        # Mercator world. The JS fitBounds supersedes this with the exact
        # pixel-based fit once rendered.
        lon_span = max(abs(ne[0] - sw[0]), 1e-9)
        lat_span = max(abs(ne[1] - sw[1]), 1e-9)
        zoom = math.log2(360.0 / max(lon_span, lat_span * 2))
        self.zoom = max(0.0, min(20.0, zoom))

        self._fit_bounds_seq += 1
        self.fit_bounds_request = {
            "bounds": [list(sw), list(ne)],
            "padding": padding,
            "_seq": self._fit_bounds_seq,
        }

    @property
    def layers(self) -> list[BaseLayer]:
        """Return the current list of layers."""
        return list(self._layers)

    @property
    def bounds(self) -> tuple[tuple[float, float], tuple[float, float]] | None:
        """Visible map extent as ``((west, south), (east, north))`` — lower-left, upper-right.

        Reported by the frontend (MapLibre ``map.getBounds()``) together with the
        other ``viewport`` fields when the map finishes loading and after every
        camera move. ``None`` until the frontend has reported once (e.g. before
        the widget is displayed, or in a plain-Python/export context).

        The shape matches what :meth:`fit_bounds` accepts, so
        ``m.fit_bounds(m.bounds)`` round-trips. Also available as
        ``widget.value["viewport"]["bounds"]`` for reactive cells.

        Notes
        -----
        - With ``pitch > 0`` the visible area is a trapezoid; this is its
          axis-aligned bounding box, which grows quickly at high pitch near
          the horizon.
        - Longitudes are *unwrapped* across the antimeridian (east may exceed
          180 or west be below -180), exactly as MapLibre reports them.
        """
        raw = self.viewport.get("bounds")
        if not raw:
            return None
        (west, south), (east, north) = raw
        return ((float(west), float(south)), (float(east), float(north)))

    def as_widget(self) -> Any:
        """Wrap this Map in ``marimo.ui.anywidget`` for reactive ``.value`` access.

        Equivalent to ``marimo.ui.anywidget(map)``; provided so users do not
        need to import marimo themselves at the call site. ``marimo`` is
        imported lazily, so this method only works inside a marimo-equipped
        environment — Jupyter / plain-Python users keep using the Map widget
        directly.
        """
        try:
            import marimo as mo
        except ImportError as err:
            raise ImportError(
                "Map.as_widget() requires marimo, which is no longer a hard "
                "dependency of deckgl-marimo. Install it with "
                "`pip install 'deckgl-marimo[marimo]'` (or `pip install marimo`). "
                "Outside marimo, use the Map widget directly."
            ) from err

        return mo.ui.anywidget(self)

    def _sync_layers(self) -> None:
        """Re-serialize all layers and update the traitlet."""
        self._pick_rows_cache.clear()
        self.layer_specs = [spec for layer in self._layers for spec in layer.to_specs()]
        self._sync_binary()

    def _sync_binary(self) -> None:
        """Pack binary data for layers that use binary mode."""
        meta, data = self._pack_binary(self._layers)
        self.binary_metadata = meta
        self.binary_data = data
