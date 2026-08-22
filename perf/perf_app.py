"""Parameterized performance-baseline notebook for deckgl-marimo.

Run with env vars:
    PERF_SCENARIO = scatter | polygon | hexagon | lifecycle
    PERF_N        = row count (int)
    PERF_MODE     = binary | json

Example:
    PERF_SCENARIO=scatter PERF_N=250000 PERF_MODE=binary \
        uv run marimo run perf/perf_app.py --headless --port 2718

The notebook exposes Python-side timings in a <pre id="py-metrics"> element
so a browser harness can scrape them. Data generation uses a fixed seed and
is timed separately (excluded from library metrics).
"""

import marimo

app = marimo.App(width="full")


@app.cell
def _():
    import json
    import os
    import time

    import numpy as np

    import marimo as mo
    import deckgl_marimo as dgl

    SCENARIO = os.environ.get("PERF_SCENARIO", "scatter")
    N = int(os.environ.get("PERF_N", "250000"))
    MODE = os.environ.get("PERF_MODE", "binary")
    return MODE, N, SCENARIO, dgl, json, mo, np, time


@app.cell
def _(N, SCENARIO, np, time):
    # Data generation (fixed seed, timed separately — not a library metric)
    _t0 = time.perf_counter()
    _rng = np.random.default_rng(42)

    if SCENARIO in ("scatter", "hexagon", "lifecycle"):
        _lon = _rng.uniform(-124.0, -67.0, N)
        _lat = _rng.uniform(25.0, 49.0, N)
        _col = _rng.integers(0, 256, (N, 3))
        _rad = _rng.uniform(1.0, 5.0, N)
        records = [
            {
                "lon": float(_lon[_i]),
                "lat": float(_lat[_i]),
                "color": [int(_col[_i, 0]), int(_col[_i, 1]), int(_col[_i, 2]), 180],
                "radius": float(_rad[_i]),
            }
            for _i in range(N)
        ]
    elif SCENARIO == "polygon":
        _side = 0.02
        _x = _rng.uniform(-124.0, -67.0, N)
        _y = _rng.uniform(25.0, 49.0, N)
        _col = _rng.integers(0, 256, (N, 3))
        records = [
            {
                "polygon": [
                    [float(_x[_i]), float(_y[_i])],
                    [float(_x[_i] + _side), float(_y[_i])],
                    [float(_x[_i] + _side), float(_y[_i] + _side)],
                    [float(_x[_i]), float(_y[_i] + _side)],
                ],
                "color": [int(_col[_i, 0]), int(_col[_i, 1]), int(_col[_i, 2]), 180],
            }
            for _i in range(N)
        ]
    else:
        records = []

    data_gen_ms = (time.perf_counter() - _t0) * 1000
    return data_gen_ms, records


@app.cell
def _(MODE, N, SCENARIO, dgl, records, time):
    # Library work: layer construction + Map construction (spec build +
    # binary packing happen inside). This is the Python-side metric.
    _t0 = time.perf_counter()
    _use_binary = MODE == "binary"

    if SCENARIO in ("scatter", "lifecycle"):
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
            use_binary=_use_binary,
        )
    elif SCENARIO == "polygon":
        layer = dgl.PolygonLayer(
            data=records,
            get_polygon="polygon",
            get_fill_color="color",
            filled=True,
            stroked=False,
            pickable=True,
            opacity=0.8,
            use_binary=_use_binary,
        )
    elif SCENARIO == "hexagon":
        layer = dgl.HexagonLayer(
            data=records,
            get_position=["lon", "lat"],
            radius=20000,
            extruded=True,
            elevation_scale=100,
            coverage=0.9,
        )
    else:
        layer = None

    m = dgl.Map(
        layers=[layer] if layer is not None else [],
        basemap="dark-matter",
        center=(-95.5, 37.0),
        zoom=3.5,
        height="600px",
    )
    build_ms = (time.perf_counter() - _t0) * 1000
    widget = m.as_widget()
    _ = N  # dependency for reactivity
    return build_ms, layer, m, widget


@app.cell
def _(MODE, N, SCENARIO, build_ms, data_gen_ms, json, m, mo):
    _payload = {
        "scenario": SCENARIO,
        "n": N,
        "mode": MODE,
        "data_gen_ms": round(data_gen_ms, 1),
        "layer_map_build_ms": round(build_ms, 1),
        "binary_bytes": len(m.binary_data),
        "spec_json_bytes": len(json.dumps(m.layer_specs).encode("utf-8")),
    }
    mo.Html(
        f'<pre id="py-metrics" style="font-size:11px">{json.dumps(_payload)}</pre>'
    )
    return


@app.cell
def _(SCENARIO, mo):
    slider = (
        mo.ui.slider(1, 20, value=5, step=1, label="radius scale", show_value=True)
        if SCENARIO == "lifecycle"
        else None
    )
    slider
    return (slider,)


@app.cell
def _(SCENARIO, json, layer, m, mo, slider, time):
    # Lifecycle scenario: slider drives update_layer -> full re-sync.
    # Python-side cost of the update is exposed in #py-update-metrics.
    _out = None
    if SCENARIO == "lifecycle" and slider is not None and slider.value != 5:
        _t0 = time.perf_counter()
        m.update_layer(layer.id, radius_scale=slider.value)
        _update_ms = (time.perf_counter() - _t0) * 1000
        _out = mo.Html(
            f'<pre id="py-update-metrics" style="font-size:11px">'
            f'{json.dumps({"radius_scale": slider.value, "update_ms": round(_update_ms, 1)})}</pre>'
        )
    _out
    return


@app.cell
def _(widget):
    widget
    return


if __name__ == "__main__":
    app.run()
