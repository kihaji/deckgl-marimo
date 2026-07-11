"""Declarative binary-attribute support for layer classes.

Each binary-capable layer declares a ``BINARY_ATTRIBUTES`` table mapping
deck.gl accessor names to (fast-path dict key, source prop, kind). One
generic implementation then drives both:

- ``to_spec()`` accessor stripping (accessors provided by binary data must
  not also appear in the JSON spec), and
- ``to_binary()`` packing for fixed-size (one value per row) layers, with a
  numpy fast path (pre-built arrays in a dict) and a list-of-dicts slow path.

Variable-length layers (Path, Polygon) keep custom ``to_binary`` but reuse
:func:`strip_binary_accessors`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar

# dtype for each attribute kind
_KIND_DTYPE = {
    "position": "float32",
    "color": "uint8",
    "value": "float32",
}


@dataclass(frozen=True)
class BinaryAttr:
    """One binary attribute of a layer.

    Parameters
    ----------
    accessor
        deck.gl accessor name in the spec, e.g. ``"getPosition"``.
    fast_key
        Key holding a pre-built numpy array on the fast-path data dict,
        e.g. ``"positions"``.
    prop
        snake_case accessor prop whose value describes the source column(s)
        on the slow path, e.g. ``"get_position"``.
    kind
        ``"position"`` (float32 vector from column list or per-row pairs),
        ``"color"`` (uint8 RGBA from a column, ColorScale, or callable), or
        ``"value"`` (float32 scalar/vector from a column).
    required
        Whether packing is impossible without this attribute.
    """

    accessor: str
    fast_key: str
    prop: str
    kind: str
    required: bool = False


def strip_binary_accessors(spec: dict, accessors: tuple[str, ...] | list[str]) -> None:
    """Remove accessor props that binary data provides from a spec, in place.

    Only column references are stripped (a column-name string, a list of
    column names, or a per-row list of values); constants stay in the spec
    so deck.gl applies them uniformly.
    """
    for key in accessors:
        val = spec.get(key)
        if isinstance(val, str) or (
            isinstance(val, list)
            and (all(isinstance(x, str) for x in val) or (len(val) > 0 and isinstance(val[0], list)))
        ):
            spec.pop(key, None)


def _attr_size(arr: Any, kind: str) -> int:
    """Components per element, derived from the array shape."""
    ndim = getattr(arr, "ndim", None)
    if ndim == 2:
        return int(arr.shape[1])
    if ndim == 1:
        return 1
    # Plain sequences (fast path given lists): peek at the first element
    first = arr[0] if len(arr) else None
    if isinstance(first, (list, tuple)):
        return len(first)
    return 1


def _extract_slow(attr: BinaryAttr, source: Any, rows: list[dict], n: int) -> Any | None:
    """Build the numpy array for one attribute from list-of-dicts rows.

    Returns None when the attribute cannot be packed from this source
    (e.g. a constant, or an unsupported accessor form) — optional
    attributes are then skipped and constants stay in the spec.
    """
    import numpy as np

    if attr.kind == "position":
        if isinstance(source, list) and all(isinstance(c, str) for c in source):
            return np.array([[row[c] for c in source] for row in rows], dtype=np.float32)
        if isinstance(source, str):
            return np.array([row[source] for row in rows], dtype=np.float32)
        return None

    if attr.kind == "color":
        if isinstance(source, str):
            colors = np.array([row[source] for row in rows], dtype=np.uint8)
            if colors.ndim == 2 and colors.shape[1] == 3:
                colors = np.hstack([colors, np.full((n, 1), 255, dtype=np.uint8)])
            return colors
        from deckgl_marimo._color_scale import resolve_color_accessor

        return resolve_color_accessor(source, rows, n)

    # kind == "value"
    if isinstance(source, str):
        return np.array([row[source] for row in rows], dtype=np.float32)
    return None


class BinaryAttributesMixin:
    """Generic ``to_spec``/``to_binary`` for fixed-size binary layers.

    Subclasses declare ``BINARY_ATTRIBUTES``; everything else is shared.
    Layers with variable-length geometry (Path, Polygon) override
    ``to_binary`` themselves.
    """

    BINARY_ATTRIBUTES: ClassVar[tuple[BinaryAttr, ...]] = ()

    if TYPE_CHECKING:
        # Provided by BaseLayer — the mixin is always combined with it.
        id: str
        data: Any
        use_binary: bool
        _props: dict[str, Any]

    def to_spec(self) -> dict:
        spec = super().to_spec()  # type: ignore[misc]
        if self.use_binary and self.BINARY_ATTRIBUTES:
            strip_binary_accessors(spec, [a.accessor for a in self.BINARY_ATTRIBUTES])
        return spec

    def to_binary(self) -> tuple[dict, bytes] | None:
        if not self.use_binary or self.data is None or not self.BINARY_ATTRIBUTES:
            return None
        from deckgl_marimo._binary import pack_binary

        required = [a for a in self.BINARY_ATTRIBUTES if a.required]

        # Fast path: dict of pre-built numpy arrays
        if isinstance(self.data, dict):
            d = self.data
            if not all(a.fast_key in d for a in required):
                return None
            n = len(d[required[0].fast_key])
            attrs: dict[str, tuple[Any, str, int]] = {}
            for a in self.BINARY_ATTRIBUTES:
                arr = d.get(a.fast_key)
                if arr is None:
                    continue
                attrs[a.accessor] = (arr, _KIND_DTYPE[a.kind], _attr_size(arr, a.kind))
            meta, buf = pack_binary(n, attrs)
            meta["id"] = self.id
            return meta, buf

        # Slow path: list of dicts
        if not isinstance(self.data, list) or not self.data:
            return None
        rows = self.data
        n = len(rows)
        attrs = {}
        for a in self.BINARY_ATTRIBUTES:
            arr = _extract_slow(a, self._props.get(a.prop), rows, n)
            if arr is None:
                if a.required:
                    return None
                continue
            attrs[a.accessor] = (arr, _KIND_DTYPE[a.kind], _attr_size(arr, a.kind))
        meta, buf = pack_binary(n, attrs)
        meta["id"] = self.id
        return meta, buf
