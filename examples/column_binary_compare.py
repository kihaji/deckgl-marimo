# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "deckgl-marimo",
#     "pandas",
#     "numpy",
# ]
#
# [tool.uv.sources]
# deckgl-marimo = { path = ".." }
# ///

import marimo

__generated_with = "0.22.0"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    import deckgl_marimo as dgl

    return (dgl,)


@app.cell
def _():
    import numpy as np
    import time
    import json

    return json, np, time


@app.cell
def _(np):
    def generate_columns_fast(count, seed=42):
        """Generate random columns using numpy.

        Returns (columns_list, columns_arrays) where:
        - columns_list: list of dicts for JSON mode
        - columns_arrays: dict of numpy arrays for binary fast path
        """
        rng = np.random.default_rng(seed)

        # Positions spread globally
        lons = rng.uniform(-160, 160, count).astype(np.float32)
        lats = rng.uniform(-55, 55, count).astype(np.float32)

        # Colors (n, 4) uint8
        colors_rgb = rng.integers(30, 256, (count, 3), dtype=np.uint8)
        colors = np.empty((count, 4), dtype=np.uint8)
        colors[:, :3] = colors_rgb
        colors[:, 3] = 180

        # Elevations
        elevations = rng.uniform(100, 10000, count).astype(np.float32)

        # --- Build numpy arrays for binary fast path ---
        positions = np.column_stack([lons, lats]).astype(np.float32)

        arrays = {
            "positions": positions,
            "colors": colors,
            "elevations": elevations,
        }

        # --- Build list of dicts for JSON mode ---
        columns = []
        for i in range(count):
            columns.append({
                "lon": float(lons[i]),
                "lat": float(lats[i]),
                "color": [int(colors[i, 0]), int(colors[i, 1]), int(colors[i, 2]), 180],
                "elevation": float(elevations[i]),
            })

        return columns, arrays

    return (generate_columns_fast,)


@app.cell
def _(mo):
    column_count_dropdown = mo.ui.dropdown(
        options={"100k": 100_000, "200k": 200_000, "300k": 300_000, "500k": 500_000},
        value="300k",
        label="Column count",
    )
    no_pick_switch = mo.ui.switch(value=True, label="Disable picking")
    const_color_switch = mo.ui.switch(value=False, label="Constant color")
    const_elev_switch = mo.ui.switch(value=False, label="Constant elevation")

    mo.hstack(
        [column_count_dropdown, no_pick_switch, const_color_switch, const_elev_switch],
        justify="start",
        gap=2,
    )
    return (
        column_count_dropdown,
        const_color_switch,
        const_elev_switch,
        no_pick_switch,
    )


@app.cell
def _(column_count_dropdown, generate_columns_fast, mo, time):
    count = column_count_dropdown.value
    _t0 = time.perf_counter()
    columns, column_arrays = generate_columns_fast(count)
    gen_time_ms = (time.perf_counter() - _t0) * 1000

    mo.md(f"Generated **{len(columns):,}** columns in **{gen_time_ms:.0f} ms**")
    return column_arrays, columns, count, gen_time_ms


@app.cell
def _(mo):
    mo.md("""
    ## JSON Mode (standard)
    """)
    return


@app.cell
def _(dgl, mo):
    json_map = dgl.Map(basemap="dark-matter", center=(0, 0), zoom=1, height="500px")
    json_widget = mo.ui.anywidget(json_map)
    return json_map, json_widget


@app.cell
def _(json_widget):
    json_widget
    return


@app.cell
def _(
    columns,
    const_color_switch,
    const_elev_switch,
    dgl,
    json,
    json_map,
    no_pick_switch,
    time,
):
    _t0 = time.perf_counter()

    _fill = [100, 150, 200, 180] if const_color_switch.value else "color"
    _elev = 5000 if const_elev_switch.value else "elevation"

    _spec = dgl.ColumnLayer(
        data=columns,
        get_position=["lon", "lat"],
        get_fill_color=_fill,
        get_elevation=_elev,
        radius=500,
        extruded=True,
        elevation_scale=1,
        pickable=not no_pick_switch.value,
    ).to_spec()

    _specs = [_spec]
    json_map.layer_specs = _specs

    _t1 = time.perf_counter()
    json_ser_ms = (_t1 - _t0) * 1000
    json_payload_bytes = len(json.dumps(_specs).encode("utf-8"))
    return json_payload_bytes, json_ser_ms


@app.cell
def _(mo):
    mo.md("""
    ## Binary Mode
    """)
    return


@app.cell
def _(dgl, mo):
    bin_map = dgl.Map(basemap="dark-matter", center=(0, 0), zoom=1, height="500px")
    bin_widget = mo.ui.anywidget(bin_map)
    return bin_map, bin_widget


@app.cell
def _(bin_widget):
    bin_widget
    return


@app.cell
def _(
    bin_map,
    column_arrays,
    const_color_switch,
    const_elev_switch,
    dgl,
    no_pick_switch,
    time,
):
    from deckgl_marimo._binary import pack_binary

    _t0 = time.perf_counter()

    _layer = dgl.ColumnLayer(
        get_fill_color=[100, 150, 200, 180],
        get_elevation=5000,
        radius=500,
        extruded=True,
        elevation_scale=1,
        pickable=not no_pick_switch.value,
        use_binary=True,
    )
    _spec = _layer.to_spec()

    _arrays = column_arrays
    attrs = {
        "getPosition": (_arrays["positions"], "float32", 2),
    }
    if not const_color_switch.value:
        attrs["getFillColor"] = (_arrays["colors"], "uint8", 4)
    if not const_elev_switch.value:
        attrs["getElevation"] = (_arrays["elevations"], "float32", 1)
    _meta, _buf = pack_binary(len(_arrays["positions"]), attrs)
    _meta["id"] = _spec["id"]

    # Set binary data BEFORE layer_specs
    bin_map.binary_metadata = {"layers": [_meta]}
    bin_map.binary_data = _buf
    bin_map.layer_specs = [_spec]

    _t1 = time.perf_counter()
    bin_ser_ms = (_t1 - _t0) * 1000
    bin_payload_bytes = len(_buf)
    return bin_payload_bytes, bin_ser_ms


@app.cell
def _(
    bin_payload_bytes,
    bin_ser_ms,
    bin_widget,
    count,
    gen_time_ms,
    json_payload_bytes,
    json_ser_ms,
    json_widget,
    mo,
):
    json_perf = json_widget.value.get("perf_metrics", {})
    bin_perf = bin_widget.value.get("perf_metrics", {})

    def _fmt_size(b):
        if b < 1024 * 1024:
            return f"{b / 1024:.1f} KB"
        return f"{b / (1024 * 1024):.1f} MB"

    def _fmt_val(v):
        return v if v != "—" else "—"

    j_fps = _fmt_val(json_perf.get("fps", "—"))
    b_fps = _fmt_val(bin_perf.get("fps", "—"))
    j_ft = _fmt_val(json_perf.get("frameTimeAvg", "—"))
    b_ft = _fmt_val(bin_perf.get("frameTimeAvg", "—"))

    speedup = ""
    if isinstance(json_ser_ms, (int, float)) and isinstance(bin_ser_ms, (int, float)) and bin_ser_ms > 0:
        speedup = f" ({json_ser_ms / bin_ser_ms:.1f}x faster)"

    mo.md(f"""
    ### Comparison — {count:,} columns

    | Metric | JSON | Binary | Notes |
    |--------|------|--------|-------|
    | **Data generation** | {gen_time_ms:.0f} ms | {gen_time_ms:.0f} ms | Same data |
    | **Serialization** | {json_ser_ms:.0f} ms | {bin_ser_ms:.0f} ms | {speedup} |
    | **Payload size** | {_fmt_size(json_payload_bytes)} | {_fmt_size(bin_payload_bytes)} | {json_payload_bytes / max(bin_payload_bytes, 1):.1f}x smaller |
    | **FPS** | {j_fps} | {b_fps} | |
    | **Frame time** | {j_ft} ms | {b_ft} ms | |
    """)
    return


@app.cell
def _(
    bin_payload_bytes,
    bin_ser_ms,
    bin_widget,
    const_color_switch,
    const_elev_switch,
    count,
    json_payload_bytes,
    json_ser_ms,
    json_widget,
    mo,
    no_pick_switch,
    set_history,
):
    def _snapshot():
        jp = json_widget.value.get("perf_metrics", {})
        bp = bin_widget.value.get("perf_metrics", {})
        row = {
            "Columns": count,
            "JSON Ser (ms)": round(json_ser_ms, 1),
            "Bin Ser (ms)": round(bin_ser_ms, 1),
            "JSON Size (MB)": round(json_payload_bytes / (1024 * 1024), 1),
            "Bin Size (MB)": round(bin_payload_bytes / (1024 * 1024), 1),
            "JSON FPS": jp.get("fps", "—"),
            "Bin FPS": bp.get("fps", "—"),
            "Picking off": no_pick_switch.value,
            "Const color": const_color_switch.value,
            "Const elevation": const_elev_switch.value,
        }
        set_history(lambda h: h + [row])

    snapshot_button = mo.ui.button(label="Capture snapshot", on_click=lambda _: _snapshot())
    snapshot_button
    return


@app.cell
def _(mo):
    get_history, set_history = mo.state([])
    return get_history, set_history


@app.cell
def _(get_history, mo):
    import pandas as pd

    history = get_history()
    if history:
        df = pd.DataFrame(history)
        _out = mo.vstack([mo.md("### Benchmark History"), mo.ui.table(df)])
    else:
        _out = mo.md("*Click 'Capture snapshot' to record metrics.*")
    _out
    return


if __name__ == "__main__":
    app.run()
