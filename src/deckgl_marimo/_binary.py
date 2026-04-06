"""Binary data packing for deck.gl layers.

Converts layer data to flat typed arrays packed into a single bytes buffer.
This bypasses JSON serialization and lets deck.gl consume data via its native
``data.attributes`` binary format.
"""

from __future__ import annotations

from typing import Any

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
