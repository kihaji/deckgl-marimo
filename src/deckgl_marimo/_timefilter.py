"""Time-filter helpers for the animated GPU time slider.

These pair with the ``Map(time_filter=...)`` prop and a layer's
``get_filter_value`` accessor (GPU ``DataFilterExtension``). Filtering and
the playback animation run entirely client-side at 60fps; the widget only
reports the throttled ``current_time`` back to Python.

``compute_time_domain`` finds the ``[t_min, t_max]`` extent of a dataset;
``build_time_filter`` assembles the ``time_filter`` dict.

Ported from deckgl_dash's ``timefilter.py``.

Float32 note
------------
``DataFilterExtension`` uploads filter values as 32-bit floats, so keep
time values float32-safe (e.g. *seconds/days since the domain start*
rather than raw epoch seconds).

Example
-------
::

    domain = dgl.compute_time_domain(points, "t")
    tf = dgl.build_time_filter(domain, window=(domain[1] - domain[0]) * 0.1, playing=True)
    m = dgl.Map(layers=[scatter], time_filter=tf)
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from deckgl_marimo._data import materialize_rows

# An accessor is a dict key, a dotted path ("properties.t"), or a callable item -> number.
TimeAccessor = str | Callable[[Any], Any]


def _resolve_items(data: Any) -> Any:
    """Return the iterable of records, unwrapping frames and FeatureCollections."""
    if isinstance(data, dict) and "features" in data:
        return data["features"]
    if isinstance(data, list):
        return data
    rows = materialize_rows(data)
    if rows is None:
        raise TypeError(
            "compute_time_domain: cannot iterate this data; provide concrete "
            "tabular data (DataFrame, list of dicts, GeoJSON), not a URL."
        )
    return rows


def _make_getter(accessor: TimeAccessor) -> Callable[[Any], Any]:
    """Build an item -> value getter from a key, dotted path, or callable."""
    if callable(accessor):
        return accessor
    if isinstance(accessor, str):
        parts = accessor.split(".")

        def _get(item: Any) -> Any:
            current = item
            for part in parts:
                if current is None:
                    return None
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    current = getattr(current, part, None)
            return current

        return _get
    raise TypeError(f"accessor must be a str or callable, got {type(accessor).__name__}")


def compute_time_domain(data: Any, accessor: TimeAccessor) -> list[float]:
    """Compute ``[t_min, t_max]`` over ``data`` using ``accessor``.

    Parameters
    ----------
    data
        A list of records (dicts or objects), a GeoJSON FeatureCollection,
        or any tabular data the library accepts (DataFrame, DuckDB, ...).
    accessor
        A dict key, a dotted path (e.g. ``"properties.t"``), or a callable
        mapping each item to its numeric time value.

    Returns
    -------
    list[float]
        ``[t_min, t_max]``.

    Raises
    ------
    ValueError
        If no numeric time values are found.
    """
    getter = _make_getter(accessor)
    t_min: float | None = None
    t_max: float | None = None
    for item in _resolve_items(data):
        value = getter(item)
        if value is None or isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        v = float(value)
        if t_min is None or v < t_min:
            t_min = v
        if t_max is None or v > t_max:
            t_max = v
    if t_min is None or t_max is None:
        raise ValueError("compute_time_domain: no numeric time values found in data")
    return [t_min, t_max]


def build_time_filter(
    domain: Sequence[float],
    window: float,
    *,
    current: float | None = None,
    playing: bool = False,
    speed: float | None = None,
    loop: bool = True,
    soft_edge: float | None = None,
    layer_ids: Sequence[str] | None = None,
    nonce: int | None = None,
) -> dict:
    """Assemble a ``time_filter`` dict for ``Map(time_filter=...)``.

    Parameters
    ----------
    domain
        ``[t_min, t_max]`` full time extent (e.g. from
        :func:`compute_time_domain`).
    window
        Sliding-window width; visible data is ``[current - window, current]``.
    current
        Initial head time. Defaults to ``domain[0] + window`` (first full
        window).
    playing
        Start the animation immediately.
    speed
        Time units advanced per wall-clock second. Defaults to a full
        sweep in ~20s.
    loop
        Wrap the head back to ``domain[0] + window`` at the end.
    soft_edge
        Optional fade width mapped to ``filterSoftRange`` for fade in/out.
    layer_ids
        Explicit target layer IDs. Defaults to auto-detecting any layer
        with a DataFilterExtension (i.e. any layer given
        ``get_filter_value``).
    nonce
        Bump to force the frontend to re-sync an unchanged ``current``.

    Returns
    -------
    dict
        Suitable for ``Map(time_filter=...)`` or assignment to the
        ``time_filter`` traitlet. Keys with ``None`` values are omitted.
    """
    t_min, t_max = float(domain[0]), float(domain[1])
    result = {
        "domain": [t_min, t_max],
        "window": window,
        "current": current if current is not None else t_min + window,
        "playing": playing,
        "speed": speed if speed is not None else (t_max - t_min) / 20.0,
        "loop": loop,
        "softEdge": soft_edge,
        "layerIds": list(layer_ids) if layer_ids is not None else None,
        "nonce": nonce,
    }
    return {k: v for k, v in result.items() if v is not None}
