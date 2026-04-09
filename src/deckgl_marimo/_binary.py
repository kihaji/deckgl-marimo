"""Binary data packing for deck.gl layers.

Converts layer data to flat typed arrays packed into a single bytes buffer.
This bypasses JSON serialization and lets deck.gl consume data via its native
``data.attributes`` binary format.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from deckgl_marimo._utils import to_camel_case


# ---------------------------------------------------------------------------
# Declarative binary attribute descriptors
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BinaryAttr:
    """Declares one binary attribute for a deck.gl layer.

    Parameters
    ----------
    accessor
        Snake_case parameter name, e.g. ``"get_position"``.
        The camelCase deck.gl name is derived automatically.
    dtype
        Numpy dtype string (``"float32"``, ``"uint8"``, etc.).
    size
        Components per element (2 for ``[lon, lat]``, 4 for RGBA, 1 for scalar).
        Use 0 to infer from the data shape (e.g. PointCloudLayer 2D vs 3D).
    fast_key
        Key in the fast-path dict (pre-built numpy arrays), e.g. ``"positions"``.
    is_geometry
        If ``True``, this is a variable-length geometry attribute (paths, polygons).
        Coordinates are flattened and ``start_indices`` are computed automatically.
    per_vertex
        For variable-length layers: expand per-object values to per-vertex.
    """

    accessor: str
    dtype: str = "float32"
    size: int = 2
    fast_key: str | None = None
    is_geometry: bool = False
    per_vertex: bool = False


@dataclass(frozen=True, slots=True)
class BinaryConfig:
    """Full binary configuration for a layer type.

    Parameters
    ----------
    attrs
        Tuple of :class:`BinaryAttr` descriptors.
    binary_type_override
        If set, ``to_spec()`` emits this layer type instead of ``LAYER_TYPE``
        when ``use_binary`` is ``True`` (e.g. PolygonLayer -> SolidPolygonLayer).
    """

    attrs: tuple[BinaryAttr, ...]
    binary_type_override: str | None = None


# ---------------------------------------------------------------------------
# Low-level buffer packing
# ---------------------------------------------------------------------------

# Numpy dtype string -> (JS dtype name, byte alignment)
_DTYPE_INFO = {
    "float32": ("float32", 4),
    "float64": ("float64", 8),
    "uint8": ("uint8", 1),
    "uint16": ("uint16", 2),
    "uint32": ("uint32", 4),
    "int32": ("int32", 4),
}


def pack_binary(
    n: int,
    attributes: dict[str, tuple[Any, str, int]],
    start_indices: Any | None = None,
) -> tuple[dict, bytes]:
    """Pack layer data into an aligned binary buffer for deck.gl.

    Parameters
    ----------
    n
        Number of data items (rows/features).
    attributes
        Mapping of attribute name to ``(array, dtype, size)`` where:
        - array: numpy array (flat, raveled)
        - dtype: numpy dtype string (``"float32"``, ``"uint8"``, etc.)
        - size: components per element (e.g. 2 for [lon, lat], 4 for RGBA)
    start_indices
        Optional uint32 array for variable-length data (polygons, paths).

    Returns
    -------
    tuple[dict, bytes]
        ``(metadata, buffer)`` ready for the JS ``applyBinaryData()`` function.
    """
    import numpy as np

    offset = 0
    buffers: list[bytes] = []
    meta_attrs: dict[str, dict] = {}

    def _append(data_bytes: bytes, alignment: int) -> int:
        nonlocal offset
        if alignment > 1:
            aligned = (offset + alignment - 1) & ~(alignment - 1)
            if aligned > offset:
                buffers.append(b"\x00" * (aligned - offset))
                offset = aligned
        buffers.append(data_bytes)
        start = offset
        offset += len(data_bytes)
        return start

    # startIndices (optional, for variable-length data)
    si_meta = None
    if start_indices is not None:
        si = np.asarray(start_indices, dtype=np.uint32)
        si_bytes = si.tobytes()
        si_start = _append(si_bytes, 4)
        si_meta = {"offset": si_start, "byteLength": len(si_bytes), "dtype": "uint32"}

    # Pack each attribute
    for attr_name, (array, dtype, size) in attributes.items():
        arr = np.asarray(array, dtype=dtype).ravel()
        js_dtype, align = _DTYPE_INFO[dtype]
        arr_bytes = arr.tobytes()
        arr_start = _append(arr_bytes, align)
        meta_attrs[attr_name] = {
            "offset": arr_start,
            "byteLength": len(arr_bytes),
            "dtype": js_dtype,
            "size": size,
        }

    metadata: dict[str, Any] = {
        "length": n,
        "attributes": meta_attrs,
    }
    if si_meta is not None:
        metadata["startIndices"] = si_meta

    return metadata, b"".join(buffers)


def pack_polygon_binary(
    data: list[dict] | Any,
    get_polygon: str = "polygon",
    get_fill_color: Any = None,
) -> tuple[dict, bytes]:
    """Pack polygon data into a binary buffer for deck.gl.

    Convenience wrapper around :func:`pack_binary` for polygon data.

    .. deprecated::
        Use :class:`BinaryConfig` on the layer class instead.

    Parameters
    ----------
    data
        List of dicts, or a dict with pre-built numpy arrays::

            {"polygon_coords": np.ndarray,   # (total_verts, 2) float32
             "start_indices": np.ndarray,     # (n_polygons,) uint32
             "colors": np.ndarray | None}     # (total_verts, 4) uint8

    get_polygon
        Key in each dict for the polygon coordinates.
    get_fill_color
        If a string, key for per-polygon [r, g, b, a] color.

    Returns
    -------
    tuple[dict, bytes]
    """
    import numpy as np

    # Fast path: pre-built numpy arrays
    if isinstance(data, dict) and "polygon_coords" in data:
        coords = np.asarray(data["polygon_coords"], dtype=np.float32)
        si = np.asarray(data["start_indices"], dtype=np.uint32)
        n = len(si)
        attrs: dict[str, tuple[Any, str, int]] = {
            "getPolygon": (coords, "float32", 2),
        }
        if data.get("colors") is not None:
            attrs["getFillColor"] = (data["colors"], "uint8", 4)
        return pack_binary(n, attrs, start_indices=si)

    # Slow path: list of dicts
    n = len(data)
    vert_counts = np.empty(n, dtype=np.uint32)
    for i, row in enumerate(data):
        vert_counts[i] = len(row[get_polygon])
    total_verts = int(vert_counts.sum())

    si = np.empty(n, dtype=np.uint32)
    si[0] = 0
    np.cumsum(vert_counts[:-1], out=si[1:])

    polygon_flat = np.empty(total_verts * 2, dtype=np.float32)
    idx = 0
    for row in data:
        for pt in row[get_polygon]:
            polygon_flat[idx] = pt[0]
            polygon_flat[idx + 1] = pt[1]
            idx += 2

    attrs = {"getPolygon": (polygon_flat, "float32", 2)}

    if isinstance(get_fill_color, str):
        vertex_colors = np.empty((total_verts, 4), dtype=np.uint8)
        for i, row in enumerate(data):
            c = row[get_fill_color]
            rgba = (c[0], c[1], c[2], c[3] if len(c) > 3 else 255)
            v_start = si[i]
            v_end = si[i + 1] if i + 1 < n else total_verts
            vertex_colors[v_start:v_end] = rgba
        attrs["getFillColor"] = (vertex_colors, "uint8", 4)

    return pack_binary(n, attrs, start_indices=si)


# ---------------------------------------------------------------------------
# Generic binary builder driven by BinaryConfig
# ---------------------------------------------------------------------------


def build_binary(
    layer_id: str,
    data: Any,
    props: dict[str, Any],
    config: BinaryConfig,
) -> tuple[dict, bytes] | None:
    """Build a binary buffer from layer data using a declarative config.

    Parameters
    ----------
    layer_id
        Layer identifier (added to metadata).
    data
        The layer's data (dict for fast path, list-of-dicts for slow path).
    props
        The layer's ``_props`` dict (snake_case keyword arguments).
    config
        Declarative :class:`BinaryConfig` describing the binary attributes.

    Returns
    -------
    tuple[dict, bytes] | None
        ``(metadata, buffer)`` or ``None`` if data format is unsupported.
    """
    # --- Fast path: pre-built numpy arrays in a dict ---
    if isinstance(data, dict):
        return _fast_path(layer_id, data, config)

    # --- Slow path: list of dicts ---
    if not isinstance(data, list):
        return None

    n = len(data)
    if n == 0:
        return None

    # Find geometry attr (variable-length) if any
    geom_attr = next((a for a in config.attrs if a.is_geometry), None)

    start_indices: Any | None = None
    total_verts = n

    if geom_attr is not None:
        total_verts, start_indices = _compute_start_indices(data, geom_attr, props, n)

    attrs: dict[str, tuple[Any, str, int]] = {}

    for attr in config.attrs:
        accessor_value = props.get(attr.accessor)
        camel = to_camel_case(attr.accessor)

        if attr.is_geometry:
            coords = _flatten_geometry(data, accessor_value, attr)
            size = attr.size if attr.size > 0 else (coords.shape[1] if coords.ndim == 2 else 2)
            attrs[camel] = (coords, attr.dtype, size)
        elif attr.dtype == "uint8" and attr.size == 4:
            # Color attribute
            array = _extract_color(
                accessor_value, data, n, total_verts, start_indices, attr.per_vertex,
            )
            if array is not None:
                attrs[camel] = (array, "uint8", 4)
        else:
            # Numeric attribute (position or scalar)
            array = _extract_numeric(accessor_value, data, attr)
            if array is not None:
                size = attr.size if attr.size > 0 else (array.shape[1] if array.ndim == 2 else 1)
                attrs[camel] = (array, attr.dtype, size)

    if not attrs:
        return None

    meta, buf = pack_binary(n, attrs, start_indices=start_indices)
    meta["id"] = layer_id
    return meta, buf


def _fast_path(
    layer_id: str,
    data: dict,
    config: BinaryConfig,
) -> tuple[dict, bytes] | None:
    """Build binary from a dict of pre-built numpy arrays."""
    import numpy as np

    geom_attr = next((a for a in config.attrs if a.is_geometry), None)
    start_indices: Any | None = None
    n: int | None = None

    if geom_attr is not None:
        if geom_attr.fast_key and geom_attr.fast_key in data:
            if "start_indices" not in data:
                return None
            start_indices = np.asarray(data["start_indices"], dtype=np.uint32)
            n = len(start_indices)
        else:
            return None

    attrs: dict[str, tuple[Any, str, int]] = {}

    for attr in config.attrs:
        if attr.fast_key is None or attr.fast_key not in data:
            continue
        arr = data[attr.fast_key]
        if arr is None:
            continue
        arr = np.asarray(arr)
        if n is None:
            n = len(arr)
        size = attr.size if attr.size > 0 else (arr.shape[1] if arr.ndim == 2 else 1)
        attrs[to_camel_case(attr.accessor)] = (arr, attr.dtype, size)

    if not attrs or n is None:
        return None

    meta, buf = pack_binary(n, attrs, start_indices=start_indices)
    meta["id"] = layer_id
    return meta, buf


def _compute_start_indices(
    data: list[dict], geom_attr: BinaryAttr, props: dict[str, Any], n: int,
) -> tuple[int, Any]:
    """Compute start_indices and total vertex count for variable-length data."""
    import numpy as np

    accessor_value = props.get(geom_attr.accessor)
    key = accessor_value if isinstance(accessor_value, str) else geom_attr.accessor.removeprefix("get_")

    vert_counts = np.array([len(row[key]) for row in data], dtype=np.uint32)
    total_verts = int(vert_counts.sum())
    si = np.empty(n, dtype=np.uint32)
    si[0] = 0
    if n > 1:
        np.cumsum(vert_counts[:-1], out=si[1:])
    return total_verts, si


def _flatten_geometry(
    data: list[dict], accessor_value: Any, attr: BinaryAttr,
) -> Any:
    """Flatten variable-length coordinate lists into a single array."""
    import numpy as np

    key = accessor_value if isinstance(accessor_value, str) else attr.accessor.removeprefix("get_")

    total_verts = sum(len(row[key]) for row in data)
    size = attr.size if attr.size > 0 else 2
    flat = np.empty(total_verts * size, dtype=np.float32)
    idx = 0
    for row in data:
        for pt in row[key]:
            for c in range(size):
                flat[idx] = pt[c]
                idx += 1
    return flat


def _extract_color(
    accessor_value: Any,
    data: list[dict],
    n: int,
    total_verts: int,
    start_indices: Any | None,
    per_vertex: bool,
) -> Any | None:
    """Extract a color attribute as an (n, 4) or (total_verts, 4) uint8 array."""
    import numpy as np

    from deckgl_marimo._color_scale import resolve_color_accessor

    if isinstance(accessor_value, str):
        colors = np.array([row[accessor_value] for row in data], dtype=np.uint8)
        if colors.ndim == 2 and colors.shape[1] == 3:
            colors = np.hstack([colors, np.full((n, 1), 255, dtype=np.uint8)])
        if per_vertex and start_indices is not None:
            return _expand_to_vertices(colors, start_indices, n, total_verts)
        return colors

    # ColorScale or callable
    resolved = resolve_color_accessor(accessor_value, data, n)
    if resolved is not None:
        if per_vertex and start_indices is not None:
            return _expand_to_vertices(resolved, start_indices, n, total_verts)
        return resolved

    return None


def _expand_to_vertices(
    per_object: Any, start_indices: Any, n: int, total_verts: int,
) -> Any:
    """Expand per-object (n, 4) colors to per-vertex (total_verts, 4)."""
    import numpy as np

    vertex_colors = np.empty((total_verts, 4), dtype=np.uint8)
    for i in range(n):
        v_start = start_indices[i]
        v_end = start_indices[i + 1] if i + 1 < n else total_verts
        vertex_colors[v_start:v_end] = per_object[i]
    return vertex_colors


def _extract_numeric(
    accessor_value: Any,
    data: list[dict],
    attr: BinaryAttr,
) -> Any | None:
    """Extract a numeric attribute (position or scalar) as a numpy array."""
    import numpy as np

    if isinstance(accessor_value, list) and all(isinstance(x, str) for x in accessor_value):
        return np.array(
            [[row[k] for k in accessor_value] for row in data],
            dtype=attr.dtype,
        )
    elif isinstance(accessor_value, str):
        return np.array([row[accessor_value] for row in data], dtype=attr.dtype)
    return None


def strip_binary_accessors(spec: dict, config: BinaryConfig) -> None:
    """Remove accessor keys from a layer spec that binary data provides.

    Also applies ``binary_type_override`` if set.
    """
    if config.binary_type_override:
        spec["type"] = config.binary_type_override

    for attr in config.attrs:
        camel = to_camel_case(attr.accessor)
        val = spec.get(camel)
        if _is_strippable_accessor(val):
            spec.pop(camel, None)


def _is_strippable_accessor(val: Any) -> bool:
    """True if the value is a data accessor that binary replaces."""
    if isinstance(val, str):
        return True
    if isinstance(val, list) and val:
        if all(isinstance(x, str) for x in val):
            return True
        if isinstance(val[0], list):
            return True
    return False
