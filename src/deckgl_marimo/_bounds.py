"""Geographic bounds computation for :meth:`Map.fit_bounds`.

``compute_bounds`` extracts a ``[[west, south], [east, north]]`` box from a
variety of inputs — point lists, path/polygon dicts, GeoJSON
(FeatureCollection, Feature, or geometry), and DataFrames (via the
``position`` column pair) — by recursively collecting ``[lon, lat]`` pairs.

Ported from deckgl_dash's ``bounds.py``.

Example:
    >>> compute_bounds([{"position": [-122.4, 37.8]}, {"position": [-122.3, 37.9]}])
    [[-122.4, 37.8], [-122.3, 37.9]]
    >>> m.fit_bounds(compute_bounds(df, position=["lon", "lat"]), padding=40)
"""
from __future__ import annotations

from typing import Any, Callable

from deckgl_marimo._data import materialize_rows

_Number = (int, float)
# Keys that hold coordinates in common deck.gl data shapes and GeoJSON.
_COORD_KEYS = (
    "path", "polygon", "position", "contour",
    "sourcePosition", "targetPosition", "source_position", "target_position",
    "from", "to",
)


def _is_point(x: Any) -> bool:
    """True if x is a [lon, lat(, ...)] coordinate pair (bool excluded — bool is an int subclass)."""
    return (
        isinstance(x, (list, tuple)) and len(x) >= 2
        and isinstance(x[0], _Number) and not isinstance(x[0], bool)
        and isinstance(x[1], _Number) and not isinstance(x[1], bool)
    )


def _walk(obj: Any, out: list[tuple[float, float]]) -> None:
    """Recursively collect [lon, lat] pairs from arbitrary nested coordinate structures."""
    if obj is None:
        return
    if _is_point(obj):
        out.append((float(obj[0]), float(obj[1])))
        return
    if isinstance(obj, (list, tuple)):
        for item in obj:
            _walk(item, out)
        return
    if isinstance(obj, dict):
        if "features" in obj:
            _walk(obj["features"], out)
        if "geometry" in obj:
            _walk(obj["geometry"], out)
        if "coordinates" in obj:
            _walk(obj["coordinates"], out)
        for key in _COORD_KEYS:
            if key in obj:
                _walk(obj[key], out)


def compute_bounds(
    data: Any,
    *,
    position: list[str] | None = None,
    get_coordinates: Callable[[Any], Any] | None = None,
) -> list[list[float]]:
    """Compute ``[[west, south], [east, north]]`` enclosing all coordinates in ``data``.

    Parameters
    ----------
    data
        A GeoJSON dict (FeatureCollection/Feature/geometry), a list of items
        (each a ``[lon, lat]`` pair, a dict with ``coordinates``/``path``/
        ``polygon``/``position``, or a GeoJSON Feature), or any tabular data
        the library accepts (DataFrame, DuckDB relation, ...) when combined
        with ``position``.
    position
        Column names for longitude and latitude, e.g. ``["lon", "lat"]`` —
        the same form layer ``get_position`` accessors take. Use for
        tabular data whose coordinates live in plain columns.
    get_coordinates
        Optional accessor mapping each item to its coordinate(s); use when
        coordinates live under a non-standard key.

    Returns
    -------
    list[list[float]]
        ``[[west, south], [east, north]]``.

    Raises
    ------
    ValueError
        If no coordinates are found.
    """
    points: list[tuple[float, float]] = []
    if position is not None:
        rows = materialize_rows(data)
        if rows is None:
            raise ValueError(
                "compute_bounds: cannot materialize rows from this data; "
                "position= requires concrete tabular data (not a URL)."
            )
        lon_col, lat_col = position[0], position[1]
        _walk([[row[lon_col], row[lat_col]] for row in rows], points)
    elif get_coordinates is not None:
        items = data["features"] if isinstance(data, dict) and "features" in data else data
        for item in items:
            _walk(get_coordinates(item), points)
    else:
        _walk(data, points)

    if not points:
        raise ValueError("compute_bounds: no coordinates found in data")

    lons = [p[0] for p in points]
    lats = [p[1] for p in points]
    return [[min(lons), min(lats)], [max(lons), max(lats)]]
