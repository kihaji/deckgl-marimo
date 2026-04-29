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
    def generate_points_fast(count, seed=42):
        """Generate random 3D points using numpy.

        Returns (points_list, points_arrays) where:
        - points_list: list of dicts for JSON mode
        - points_arrays: dict of numpy arrays for binary fast path
        """
        rng = np.random.default_rng(seed)

        # 3D positions: x,y spread globally, z random 0-10000
        xs = rng.uniform(-160, 160, count).astype(np.float32)
        ys = rng.uniform(-55, 55, count).astype(np.float32)
        zs = rng.uniform(0, 10000, count).astype(np.float32)

        # Colors (n, 4) uint8
        colors_rgb = rng.integers(30, 256, (count, 3), dtype=np.uint8)
        colors = np.empty((count, 4), dtype=np.uint8)
        colors[:, :3] = colors_rgb
        colors[:, 3] = 180

        # Normals: all pointing up for simplicity
        normals = np.zeros((count, 3), dtype=np.float32)
        normals[:, 2] = 1.0

        # --- Build numpy arrays for binary fast path ---
        positions = np.column_stack([xs, ys, zs]).astype(np.float32)

        arrays = {
            "positions": positions,
            "colors": colors,
            "normals": normals,
        }

        # --- Build list of dicts for JSON mode ---
        points = []
        for i in range(count):
            points.append({
                "position": [float(xs[i]), float(ys[i]), float(zs[i])],
                "color": [int(colors[i, 0]), int(colors[i, 1]), int(colors[i, 2]), 180],
                "normal": [0.0, 0.0, 1.0],
            })

        return points, arrays

    return (generate_points_fast,)


@app.cell
def _(mo):
    point_count_dropdown = mo.ui.dropdown(
        options={"100k": 100_000, "250k": 250_000, "500k": 500_000, "1M": 1_000_000},
        value="500k",
        label="Point count",
    )
    no_pick_switch = mo.ui.switch(value=True, label="Disable picking")
    const_color_switch = mo.ui.switch(value=False, label="Constant color")

    mo.hstack(
        [point_count_dropdown, no_pick_switch, const_color_switch],
        justify="start",
        gap=2,
    )
    return const_color_switch, no_pick_switch, point_count_dropdown


@app.cell
def _(generate_points_fast, mo, point_count_dropdown, time):
    count = point_count_dropdown.value
    _t0 = time.perf_counter()
    points, point_arrays = generate_points_fast(count)
    gen_time_ms = (time.perf_counter() - _t0) * 1000

    mo.md(f"Generated **{len(points):,}** points in **{gen_time_ms:.0f} ms**")
    return count, gen_time_ms, point_arrays, points


@app.cell
def _(mo):
    mo.md("""
    ## JSON Mode (standard)
    """)
    return


@app.cell
def _(dgl, mo):
    json_map = dgl.Map(basemap="dark-matter", center=(0, 0), zoom=1, height="500px")
    json_widget = json_map.as_widget()
    return json_map, json_widget


@app.cell
def _(json_widget):
    json_widget
    return


@app.cell
def _(
    const_color_switch,
    dgl,
    json,
    json_map,
    no_pick_switch,
    points,
    time,
):
    _t0 = time.perf_counter()

    _color = [100, 150, 200, 180] if const_color_switch.value else "color"

    _spec = dgl.PointCloudLayer(
        data=points,
        get_position="position",
        get_color=_color,
        get_normal="normal",
        point_size=2,
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
    bin_widget = bin_map.as_widget()
    return bin_map, bin_widget


@app.cell
def _(bin_widget):
    bin_widget
    return


@app.cell
def _(
    bin_map,
    const_color_switch,
    dgl,
    no_pick_switch,
    point_arrays,
    time,
):
    from deckgl_marimo._binary import pack_binary

    _t0 = time.perf_counter()

    _layer = dgl.PointCloudLayer(
        get_color=[100, 150, 200, 180],
        point_size=2,
        pickable=not no_pick_switch.value,
        use_binary=True,
    )
    _spec = _layer.to_spec()

    _arrays = point_arrays
    attrs = {
        "getPosition": (_arrays["positions"], "float32", 3),
    }
    if not const_color_switch.value:
        attrs["getColor"] = (_arrays["colors"], "uint8", 4)
    attrs["getNormal"] = (_arrays["normals"], "float32", 3)
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
    ### Comparison — {count:,} points

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
            "Points": count,
            "JSON Ser (ms)": round(json_ser_ms, 1),
            "Bin Ser (ms)": round(bin_ser_ms, 1),
            "JSON Size (MB)": round(json_payload_bytes / (1024 * 1024), 1),
            "Bin Size (MB)": round(bin_payload_bytes / (1024 * 1024), 1),
            "JSON FPS": jp.get("fps", "—"),
            "Bin FPS": bp.get("fps", "—"),
            "Picking off": no_pick_switch.value,
            "Const color": const_color_switch.value,
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
