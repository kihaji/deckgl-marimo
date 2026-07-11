"""Map widget for deckgl-marimo."""

from __future__ import annotations

import pathlib
from typing import Any, ClassVar

import anywidget
import traitlets

from deckgl_marimo._base import BaseLayer, _raise_for_unknown_props
from deckgl_marimo._basemaps import Basemaps
from deckgl_marimo._data import materialize_rows

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
        Basemap style name or URL. Use :class:`Basemaps` aliases like
        ``"dark-matter"`` or a full MapLibre style URL.
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
        "height", "width",
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

    # Layout
    height = traitlets.Unicode("600px").tag(sync=True)
    width = traitlets.Unicode("100%").tag(sync=True)

    # Binary data transfer (bypasses JSON serialization)
    binary_data = traitlets.Bytes(b"").tag(sync=True)
    binary_metadata = traitlets.Dict({}).tag(sync=True)

    # Read-back from JS (JS -> Python)
    viewport = traitlets.Dict({}).tag(sync=True)
    click_info = traitlets.Dict({}).tag(sync=True)
    hover_info = traitlets.Dict({}).tag(sync=True)
    perf_metrics = traitlets.Dict({}).tag(sync=True)

    def __init__(
        self,
        layers: list[BaseLayer] | None = None,
        *,
        basemap: str = "dark-matter",
        center: tuple[float, float] | None = None,
        zoom: float = 1.0,
        pitch: float = 0.0,
        bearing: float = 0.0,
        height: str = "600px",
        width: str = "100%",
        _unsafe_props: bool = False,
        **kwargs: Any,
    ) -> None:
        if not _unsafe_props:
            _raise_for_unknown_props(type(self).__name__, kwargs, self._VALID_KWARGS)
        self._layers: list[BaseLayer] = list(layers or [])
        self._resolving_pick = False
        specs = [spec for layer in self._layers for spec in layer.to_specs()]
        style = Basemaps.resolve(basemap)

        # Pre-pack binary data for layers that use binary mode
        bin_meta, bin_data = self._pack_binary(self._layers)

        init_kwargs: dict[str, Any] = {
            "layer_specs": specs,
            "basemap_style": style,
            "binary_data": bin_data,
            "binary_metadata": bin_meta,
            "zoom": zoom,
            "pitch": pitch,
            "bearing": bearing,
            "height": height,
            "width": width,
            **kwargs,
        }

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
        rows = materialize_rows(layer.data)
        if rows is None or index >= len(rows):
            return
        self._resolving_pick = True
        try:
            setattr(self, change["name"], {**info, "object": rows[index]})
        finally:
            self._resolving_pick = False

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
            Properties to update (snake_case).
        """
        for layer in self._layers:
            if layer.id == layer_id:
                for key, value in props.items():
                    if hasattr(layer, key):
                        setattr(layer, key, value)
                    else:
                        layer._props[key] = value
                break
        self._sync_layers()

    def fit_bounds(self, bounds: list[list[float]]) -> None:
        """Set the view to fit the given bounds.

        Parameters
        ----------
        bounds
            [[sw_longitude, sw_latitude], [ne_longitude, ne_latitude]]
        """
        sw, ne = bounds
        self.longitude = (sw[0] + ne[0]) / 2
        self.latitude = (sw[1] + ne[1]) / 2

    @property
    def layers(self) -> list[BaseLayer]:
        """Return the current list of layers."""
        return list(self._layers)

    def as_widget(self) -> Any:
        """Wrap this Map in ``marimo.ui.anywidget`` for reactive ``.value`` access.

        Equivalent to ``marimo.ui.anywidget(map)``; provided so users do not
        need to import marimo themselves at the call site. ``marimo`` is
        imported lazily, so this method only works inside a marimo-equipped
        environment — Jupyter / plain-Python users keep using the Map widget
        directly.
        """
        import marimo as mo

        return mo.ui.anywidget(self)

    def _sync_layers(self) -> None:
        """Re-serialize all layers and update the traitlet."""
        self.layer_specs = [spec for layer in self._layers for spec in layer.to_specs()]
        self._sync_binary()

    def _sync_binary(self) -> None:
        """Pack binary data for layers that use binary mode."""
        meta, data = self._pack_binary(self._layers)
        self.binary_metadata = meta
        self.binary_data = data
