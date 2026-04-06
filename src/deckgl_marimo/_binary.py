"""Binary data packing for deck.gl layers.

Converts polygon data to flat typed arrays packed into a single bytes buffer.
This bypasses JSON serialization and lets deck.gl consume data via its native
``data.attributes`` binary format.
"""

from __future__ import annotations

from typing import Any


def pack_polygon_binary(
    data: list[dict] | Any,
    get_polygon: str = "polygon",
    get_fill_color: Any = None,
) -> tuple[dict, bytes]:
    """Pack polygon data into a binary buffer for deck.gl.

    Parameters
    ----------
    data
        List of dicts, each with a polygon key containing [[lon, lat], ...].
        For best performance, pass a dict with pre-built numpy arrays::

            {"polygon_coords": np.ndarray,   # (total_verts, 2) float32
             "start_indices": np.ndarray,     # (n_polygons,) uint32
             "colors": np.ndarray | None}     # (total_verts, 4) uint8

    get_polygon
        Key in each dict for the polygon coordinates (ignored for array input).
    get_fill_color
        If a string, treated as a key in each dict for [r, g, b, a] color.
        Ignored for array input.

    Returns
    -------
    tuple[dict, bytes]
        (metadata, buffer) where metadata describes the layout of typed
        arrays in the buffer and buffer is the packed bytes.
    """
    import numpy as np

    # Fast path: pre-built numpy arrays
    if isinstance(data, dict) and "polygon_coords" in data:
        coords = np.asarray(data["polygon_coords"], dtype=np.float32)
        start_indices = np.asarray(data["start_indices"], dtype=np.uint32)
        n = len(start_indices)
        color_array = None
        if data.get("colors") is not None:
            color_array = np.asarray(data["colors"], dtype=np.uint8).ravel()
        polygon_flat = coords.ravel()
        return _pack_buffer(n, start_indices, polygon_flat, color_array)

    # Slow path: list of dicts — extract into arrays
    n = len(data)

    # First pass: count total vertices for pre-allocation
    vert_counts = np.empty(n, dtype=np.uint32)
    for i, row in enumerate(data):
        vert_counts[i] = len(row[get_polygon])
    total_verts = int(vert_counts.sum())

    # Build start indices
    start_indices = np.empty(n, dtype=np.uint32)
    start_indices[0] = 0
    np.cumsum(vert_counts[:-1], out=start_indices[1:])

    # Flatten coordinates into pre-allocated array
    polygon_flat = np.empty(total_verts * 2, dtype=np.float32)
    idx = 0
    for row in data:
        for pt in row[get_polygon]:
            polygon_flat[idx] = pt[0]
            polygon_flat[idx + 1] = pt[1]
            idx += 2

    # Expand per-polygon colors to per-vertex
    color_array = None
    if isinstance(get_fill_color, str):
        vertex_colors = np.empty((total_verts, 4), dtype=np.uint8)
        for i, row in enumerate(data):
            c = row[get_fill_color]
            rgba = (c[0], c[1], c[2], c[3] if len(c) > 3 else 255)
            v_start = start_indices[i]
            v_end = start_indices[i + 1] if i + 1 < n else total_verts
            vertex_colors[v_start:v_end] = rgba
        color_array = vertex_colors.ravel()

    return _pack_buffer(n, start_indices, polygon_flat, color_array)


def _pack_buffer(
    n: int,
    start_indices,
    polygon_flat,
    color_array,
) -> tuple[dict, bytes]:
    """Pack arrays into a single aligned binary buffer with metadata."""
    offset = 0
    buffers: list[bytes] = []
    meta_attrs: dict[str, dict] = {}

    def _append(data_bytes: bytes, alignment: int) -> int:
        nonlocal offset
        aligned = offset
        if alignment > 1:
            aligned = (offset + alignment - 1) & ~(alignment - 1)
        if aligned > offset:
            buffers.append(b"\x00" * (aligned - offset))
            offset = aligned
        buffers.append(data_bytes)
        start = offset
        offset += len(data_bytes)
        return start

    # startIndices (uint32, 4-byte aligned)
    si_bytes = start_indices.tobytes()
    si_start = _append(si_bytes, 4)
    si_meta = {"offset": si_start, "byteLength": len(si_bytes), "dtype": "uint32"}

    # getPolygon (float32, 4-byte aligned)
    pg_bytes = polygon_flat.tobytes()
    pg_start = _append(pg_bytes, 4)
    meta_attrs["getPolygon"] = {
        "offset": pg_start,
        "byteLength": len(pg_bytes),
        "dtype": "float32",
        "size": 2,
    }

    # getFillColor (uint8, no alignment needed)
    if color_array is not None:
        fc_bytes = color_array.tobytes()
        fc_start = _append(fc_bytes, 1)
        meta_attrs["getFillColor"] = {
            "offset": fc_start,
            "byteLength": len(fc_bytes),
            "dtype": "uint8",
            "size": 4,
        }

    metadata = {
        "length": n,
        "startIndices": si_meta,
        "attributes": meta_attrs,
    }

    return metadata, b"".join(buffers)
