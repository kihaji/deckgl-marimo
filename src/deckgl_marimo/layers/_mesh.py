"""Mesh deck.gl layer wrappers."""

from __future__ import annotations

from typing import Any

from deckgl_marimo._accessors import Accessor, ColorAccessor, PositionAccessor
from deckgl_marimo._base import BaseLayer
from deckgl_marimo.layers._core import _experimental


@_experimental
class SimpleMeshLayer(BaseLayer):
    """Render 3D meshes at given positions."""

    LAYER_TYPE = "SimpleMeshLayer"

    def __init__(
        self,
        *,
        data: Any = None,
        get_position: PositionAccessor | None = None,
        get_color: ColorAccessor = (255, 0, 0, 255),
        get_orientation: Accessor = (0, 0, 0),
        mesh: Any = None,
        **kwargs: Any,
    ) -> None:
        props: dict[str, Any] = {
            "get_position": get_position,
            "get_color": list(get_color) if isinstance(get_color, tuple) else get_color,
            "get_orientation": list(get_orientation) if isinstance(get_orientation, tuple) else get_orientation,
        }
        if mesh is not None:
            props["mesh"] = mesh
        super().__init__(data=data, **props, **kwargs)


@_experimental
class ScenegraphLayer(BaseLayer):
    """Render 3D models (glTF) at given positions."""

    LAYER_TYPE = "ScenegraphLayer"

    def __init__(
        self,
        *,
        data: Any = None,
        get_position: PositionAccessor | None = None,
        get_color: ColorAccessor = (255, 255, 255, 255),
        get_orientation: Accessor = (0, 0, 0),
        scenegraph: str | None = None,
        size_scale: float = 1,
        **kwargs: Any,
    ) -> None:
        props: dict[str, Any] = {
            "get_position": get_position,
            "get_color": list(get_color) if isinstance(get_color, tuple) else get_color,
            "get_orientation": list(get_orientation) if isinstance(get_orientation, tuple) else get_orientation,
            "size_scale": size_scale,
        }
        if scenegraph is not None:
            props["scenegraph"] = scenegraph
        super().__init__(data=data, **props, **kwargs)
