"""Base layer class for deckgl-marimo."""

from __future__ import annotations

from typing import Any, ClassVar
from uuid import uuid4

from deckgl_marimo._data import prepare_data
from deckgl_marimo._utils import to_camel_case


class BaseLayer:
    """Base class for all deck.gl layer wrappers.

    Layers are plain Python objects that serialize to JSON specs via
    :meth:`to_spec`. They can also be used directly as widgets —
    passing a layer to ``mo.ui.anywidget()`` or displaying it in a
    notebook cell automatically wraps it in a :class:`Map`.

    Parameters
    ----------
    data
        Input data. Accepts pandas/polars DataFrames, GeoDataFrames,
        DuckDB Relations, list of dicts, GeoJSON dicts, or URLs.
    id
        Unique layer identifier. Auto-generated if not provided.
    visible
        Whether the layer is visible.
    opacity
        Layer opacity (0-1).
    pickable
        Whether the layer responds to pointer events.
    auto_highlight
        Whether to highlight the picked object.
    basemap
        Basemap style for standalone display (default ``"dark-matter"``).
    center
        Initial map center as ``(longitude, latitude)`` for standalone display.
    zoom
        Initial zoom level for standalone display.
    pitch
        Initial pitch for standalone display.
    bearing
        Initial bearing for standalone display.
    map_height
        CSS height for standalone display.
    **props
        Additional deck.gl layer properties in snake_case.
    """

    LAYER_TYPE: ClassVar[str] = "BaseLayer"

    # Keys that are Map parameters, not layer props
    _MAP_KEYS: ClassVar[set[str]] = {
        "basemap", "center", "zoom", "pitch", "bearing", "map_height",
    }

    def __init__(
        self,
        *,
        data: Any = None,
        id: str | None = None,
        visible: bool = True,
        opacity: float = 1.0,
        pickable: bool = True,
        auto_highlight: bool = False,
        basemap: str = "dark-matter",
        center: tuple[float, float] | None = None,
        zoom: float = 1.0,
        pitch: float = 0.0,
        bearing: float = 0.0,
        map_height: str = "600px",
        **props: Any,
    ) -> None:
        self.id = id or f"{self.LAYER_TYPE}-{uuid4().hex[:8]}"
        self.data = data
        self.visible = visible
        self.opacity = opacity
        self.pickable = pickable
        self.auto_highlight = auto_highlight
        self._props = props

        # Map parameters for standalone display
        self._map_kwargs: dict[str, Any] = {
            "basemap": basemap,
            "zoom": zoom,
            "pitch": pitch,
            "bearing": bearing,
            "height": map_height,
        }
        if center is not None:
            self._map_kwargs["center"] = center

        # Lazily created Map for anywidget protocol
        self.__map: Any = None

    def to_spec(self) -> dict:
        """Serialize to a JSON-compatible dict for the JS layer factory.

        Returns
        -------
        dict
            Layer specification with camelCase keys matching deck.gl API.
        """
        spec: dict[str, Any] = {
            "type": self.LAYER_TYPE,
            "id": self.id,
            "visible": self.visible,
            "opacity": self.opacity,
            "pickable": self.pickable,
            "autoHighlight": self.auto_highlight,
        }

        if self.data is not None:
            spec["data"] = prepare_data(self.data)

        # Convert snake_case props to camelCase
        for key, value in self._props.items():
            camel_key = to_camel_case(key)
            spec[camel_key] = value

        return spec

    def _get_map(self) -> Any:
        """Get or create the backing Map widget for anywidget compatibility."""
        if self.__map is None:
            from deckgl_marimo._map import Map

            self.__map = Map(layers=[self], **self._map_kwargs)
        return self.__map

    def __getattr__(self, name: str) -> Any:
        """Proxy anywidget protocol attributes to the backing Map.

        This allows ``mo.ui.anywidget(layer)`` to work transparently
        by delegating widget attributes (comm, _esm, _css, traits, etc.)
        to a lazily-created Map instance.
        """
        # Avoid infinite recursion for our own attributes
        if name.startswith("_BaseLayer") or name in (
            "id", "data", "visible", "opacity", "pickable",
            "auto_highlight", "_props", "_map_kwargs",
            "LAYER_TYPE", "_MAP_KEYS",
        ):
            raise AttributeError(name)

        # Delegate to the backing Map
        return getattr(self._get_map(), name)

    def _repr_mimebundle_(self, **kwargs: Any) -> Any:
        """Display standalone by wrapping in a Map."""
        return self._get_map()._repr_mimebundle_(**kwargs)

    def __repr__(self) -> str:
        return f"{self.LAYER_TYPE}(id={self.id!r})"
