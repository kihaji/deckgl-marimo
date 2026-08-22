"""Shared workload for the kernel-side performance watchdog.

Imported both by the pytest module (plain-process reference measurement) and by
``_kernel_bench_notebook.py`` (the same workload executed inside a marimo
kernel via ``marimo export html``). Keeping the workload in one place guarantees
the two measurements differ only in *where* they run.

The workload mirrors ``perf/perf_app.py``'s scatter scenario: fixed-seed
records, ``ScatterplotLayer`` + ``Map`` construction (which opens the anywidget
comm when a kernel is present), then ``update_layer`` (comm send path).
"""

from __future__ import annotations

import statistics
import time
from typing import Any

SEED = 42
DEFAULT_N = 250_000
DEFAULT_REPEATS = 3


def make_records(n: int = DEFAULT_N) -> list[dict[str, Any]]:
    """Deterministic scatter records (same shape as perf/perf_app.py)."""
    import numpy as np

    rng = np.random.default_rng(SEED)
    lon = rng.uniform(-124.0, -67.0, n)
    lat = rng.uniform(25.0, 49.0, n)
    col = rng.integers(0, 256, (n, 3))
    rad = rng.uniform(1.0, 5.0, n)
    return [
        {
            "lon": float(lon[i]),
            "lat": float(lat[i]),
            "color": [int(col[i, 0]), int(col[i, 1]), int(col[i, 2]), 180],
            "radius": float(rad[i]),
        }
        for i in range(n)
    ]


def build_map(records: list[dict[str, Any]], *, use_binary: bool) -> tuple[Any, Any]:
    """Layer + Map construction — the 'py build' metric of the perf harness."""
    import deckgl_marimo as dgl

    layer = dgl.ScatterplotLayer(
        data=records,
        get_position=["lon", "lat"],
        get_fill_color="color",
        get_radius="radius",
        radius_scale=5,
        radius_min_pixels=1,
        radius_max_pixels=10,
        opacity=0.8,
        pickable=True,
        use_binary=use_binary,
    )
    m = dgl.Map(
        layers=[layer],
        basemap="dark-matter",
        center=(-95.5, 37.0),
        zoom=3.5,
        height="600px",
    )
    return layer, m


def _time_build(records: list[dict[str, Any]], *, use_binary: bool, repeats: int) -> tuple[float, Any, Any]:
    """Median build time over ``repeats`` fresh Layer+Map constructions; returns the last pair."""
    samples: list[float] = []
    layer = m = None
    for _ in range(repeats):
        t0 = time.perf_counter()
        layer, m = build_map(records, use_binary=use_binary)
        samples.append((time.perf_counter() - t0) * 1000)
    return round(statistics.median(samples), 1), layer, m


def _time_updates(layer: Any, m: Any, *, repeats: int) -> float:
    """Median ``update_layer`` time over ``repeats`` single-prop updates (comm send path)."""
    samples: list[float] = []
    for k in range(repeats):
        t0 = time.perf_counter()
        m.update_layer(layer.id, radius_scale=6 + k)
        samples.append((time.perf_counter() - t0) * 1000)
    return round(statistics.median(samples), 1)


def bench(records: list[dict[str, Any]], *, repeats: int = DEFAULT_REPEATS) -> dict[str, Any]:
    """Run the workload and return timings (ms, medians of ``repeats``).

    Keys: ``json_build_ms``, ``json_update_ms``, ``binary_build_ms``,
    ``binary_update_ms``, ``n``, ``repeats``. The last-built JSON-mode map is
    returned under ``_map`` so a notebook can display it (not serialisable).
    """
    out: dict[str, Any] = {"n": len(records), "repeats": repeats}
    for mode, use_binary in (("json", False), ("binary", True)):
        out[f"{mode}_build_ms"], layer, m = _time_build(records, use_binary=use_binary, repeats=repeats)
        out[f"{mode}_update_ms"] = _time_updates(layer, m, repeats=repeats)
        if mode == "json":
            out["_map"] = m
    return out
