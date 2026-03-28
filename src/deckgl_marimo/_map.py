"""Map widget for deckgl-marimo."""

from __future__ import annotations

import pathlib
from typing import Any

import anywidget
import traitlets

from deckgl_marimo._base import BaseLayer
from deckgl_marimo._basemaps import Basemaps

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

    # Read-back from JS (JS -> Python)
    viewport = traitlets.Dict({}).tag(sync=True)
    click_info = traitlets.Dict({}).tag(sync=True)
    hover_info = traitlets.Dict({}).tag(sync=True)

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
        **kwargs: Any,
    ) -> None:
        self._layers: list[BaseLayer] = list(layers or [])
        specs = [layer.to_spec() for layer in self._layers]
        style = Basemaps.resolve(basemap)

        init_kwargs: dict[str, Any] = {
            "layer_specs": specs,
            "basemap_style": style,
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
        self._layers = [l for l in self._layers if l.id != layer_id]
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

    def _sync_layers(self) -> None:
        """Re-serialize all layers and update the traitlet."""
        self.layer_specs = [layer.to_spec() for layer in self._layers]
