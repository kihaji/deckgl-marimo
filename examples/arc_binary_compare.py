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
    def generate_arcs_fast(count, seed=42):
        """Generate random arcs spread globally.

        Returns (arcs_list, arcs_arrays) where:
        - arcs_list: list of dicts for JSON mode
        - arcs_arrays: dict of numpy arrays for binary fast path
        """
        rng = np.random.default_rng(seed)

        # Random source points spread globally
        src_lon = rng.uniform(-180, 180, count).astype(np.float32)
        src_lat = rng.uniform(-80, 80, count).astype(np.float32)

        # Targets offset by random 5-30 degrees
        offset_lon = rng.uniform(5, 30, count).astype(np.float32) * rng.choice([-1, 1], count).astype(np.float32)
        offset_lat = rng.uniform(5, 30, count).astype(np.float32) * rng.choice([-1, 1], count).astype(np.float32)
        tgt_lon = np.clip(src_lon + offset_lon, -180, 180)
        tgt_lat = np.clip(src_lat + offset_lat, -85, 85)

        # Per-arc colors
        src_colors = rng.integers(30, 256, (count, 3), dtype=np.uint8)
        tgt_colors = rng.integers(30, 256, (count, 3), dtype=np.uint8)

        # --- Build numpy arrays for binary fast path ---
        source_positions = np.column_stack([src_lon, src_lat]).astype(np.float32)
        target_positions = np.column_stack([tgt_lon, tgt_lat]).astype(np.float32)

        source_colors = np.empty((count, 4), dtype=np.uint8)
        source_colors[:, :3] = src_colors
        source_colors[:, 3] = 180

        target_colors = np.empty((count, 4), dtype=np.uint8)
        target_colors[:, :3] = tgt_colors
        target_colors[:, 3] = 180

        arcs_arrays = {
            "source_positions": source_positions,
            "target_positions": target_positions,
            "source_colors": source_colors,
            "target_colors": target_colors,
        }

        # --- Build list of dicts for JSON mode ---
        arcs_list = []
        for i in range(count):
            arcs_list.append({
                "src_lon": float(src_lon[i]),
                "src_lat": float(src_lat[i]),
                "tgt_lon": float(tgt_lon[i]),
                "tgt_lat": float(tgt_lat[i]),
                "src_color": [int(src_colors[i, 0]), int(src_colors[i, 1]), int(src_colors[i, 2]), 180],
                "tgt_color": [int(tgt_colors[i, 0]), int(tgt_colors[i, 1]), int(tgt_colors[i, 2]), 180],
            })

        return arcs_list, arcs_arrays

    return (generate_arcs_fast,)


@app.cell
def _(mo):
    arc_count_dropdown = mo.ui.dropdown(
        options={"100k": 100_000, "200k": 200_000, "300k": 300_000, "500k": 500_000},
        value="300k",
        label="Arc count",
    )
    no_pick_switch = mo.ui.switch(value=True, label="Disable picking")
    const_color_switch = mo.ui.switch(value=False, label="Constant color")

    mo.hstack(
        [arc_count_dropdown, no_pick_switch, const_color_switch],
        justify="start",
        gap=2,
    )
    return arc_count_dropdown, const_color_switch, no_pick_switch


@app.cell
def _(arc_count_dropdown, generate_arcs_fast, mo, time):
    count = arc_count_dropdown.value
    _t0 = time.perf_counter()
    arcs, arc_arrays = generate_arcs_fast(count)
    gen_time_ms = (time.perf_counter() - _t0) * 1000

    mo.md(f"Generated **{len(arcs):,}** arcs in **{gen_time_ms:.0f} ms**")
    return arcs, arc_arrays, count, gen_time_ms


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
def _(arcs, const_color_switch, dgl, json, json_map, no_pick_switch, time):
    _t0 = time.perf_counter()

    _src_color = [0, 128, 255, 180] if const_color_switch.value else "src_color"
    _tgt_color = [255, 0, 128, 180] if const_color_switch.value else "tgt_color"

    _spec = dgl.ArcLayer(
        data=arcs,
        get_source_position=["src_lon", "src_lat"],
        get_target_position=["tgt_lon", "tgt_lat"],
        get_source_color=_src_color,
        get_target_color=_tgt_color,
        get_width=1,
        pickable=not no_pick_switch.value,
        opacity=0.8,
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
def _(arc_arrays, bin_map, const_color_switch, dgl, no_pick_switch, time):
    from deckgl_marimo._binary import pack_binary

    _t0 = time.perf_counter()

    _layer = dgl.ArcLayer(
        get_source_color=[0, 128, 255, 180],
        get_target_color=[255, 0, 128, 180],
        get_width=1,
        pickable=not no_pick_switch.value,
        opacity=0.8,
        use_binary=True,
    )
    _spec = _layer.to_spec()

    _arrays = arc_arrays
    attrs = {
        "getSourcePosition": (_arrays["source_positions"], "float32", 2),
        "getTargetPosition": (_arrays["target_positions"], "float32", 2),
    }
    if not const_color_switch.value:
        attrs["getSourceColor"] = (_arrays["source_colors"], "uint8", 4)
        attrs["getTargetColor"] = (_arrays["target_colors"], "uint8", 4)
    _meta, _buf = pack_binary(len(_arrays["source_positions"]), attrs)
    _meta["id"] = _spec["id"]

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
    ### Comparison — {count:,} arcs

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
            "Arcs": count,
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
