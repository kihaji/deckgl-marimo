"""Repro: marimo 0.23.14 anywidget state-serialization slowdown.

marimo-team/marimo#10127 (commit 56d8ec070, first released in 0.23.14) routes
every anywidget comm open AND send through
`AnyWidgetStateSerializer.serialize()` -> `_replace_widget_refs()`, which
recursively visits every node of the widget state, probes each one with
`getattr(value, "model_id")` (+ descriptor checks) before its primitive
early-out, and rebuilds a parallel copy of every container just to compare
element identity.

For a widget with a large data trait (e.g. 250k records), that is ~1.5M node
visits and ~500k throwaway container allocations per open/update.

Run under 0.23.13 -> ImportError (module doesn't exist, and widget creation
is fast). Run under 0.23.14 -> the serialize walk below is the extra time
that appeared inside every kernel-side widget open/update.

    uv run --with marimo==0.23.14 python repro_widget_ref_perf.py
"""

import statistics
import time

N = 250_000

# Anywidget-shaped opening state with a large list-of-records trait —
# the exact shape any data-heavy anywidget (deckgl, mosaic, lonboard-style
# JSON paths) syncs.
state = {
    "_esm": "export default { render({ model, el }) {} }",
    "data": [
        {"lon": -100.0 + i * 1e-5, "lat": 40.0, "color": [255, 0, 0, 180], "value": float(i)}
        for i in range(N)
    ],
}


def time_it(fn, repeats=5):
    times = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn()
        times.append((time.perf_counter() - t0) * 1000)
    return statistics.median(times)


try:
    from marimo._plugins.ui._impl.anywidget.widget_ref import (
        AnyWidgetStateSerializer,
    )
except ImportError:
    import marimo

    print(f"marimo {marimo.__version__}: widget_ref module not present (pre-0.23.14) — not affected")
    raise SystemExit(0)

import marimo

serializer = AnyWidgetStateSerializer(state)
ms = time_it(lambda: serializer.serialize(state))
print(f"marimo {marimo.__version__}: serialize() over {N:,}-record anywidget state: {ms:.0f} ms (median of 5)")
print("This cost is paid on every comm open and every state update for the widget.")
