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
    def generate_paths(count, seed=42):
        """Generate random paths using numpy.

        Returns (paths_list, paths_arrays) where:
        - paths_list: list of dicts for JSON mode
        - paths_arrays: dict of numpy arrays for binary fast path
        """
        rng = np.random.default_rng(seed)

        verts_per_path = 15

        # Grid starting points spread across the world
        cols = int(np.ceil(np.sqrt(count)))
        rows = int(np.ceil(count / cols))
        total_cells = cols * rows

        lon_range, lat_range = 320.0, 110.0
        cell_w, cell_h = lon_range / cols, lat_range / rows

        col_idx = np.arange(total_cells) % cols
        row_idx = np.arange(total_cells) // cols
        start_lon = -160.0 + (col_idx + 0.5) * cell_w
        start_lat = -55.0 + (row_idx + 0.5) * cell_h
        start_lon = start_lon[:count]
        start_lat = start_lat[:count]

        # Generate random walk steps for each path
        step_lon = rng.uniform(-cell_w * 0.06, cell_w * 0.06, (count, verts_per_path - 1))
        step_lat = rng.uniform(-cell_h * 0.06, cell_h * 0.06, (count, verts_per_path - 1))

        # Cumulative sum to get wandering paths
        all_lons = np.empty((count, verts_per_path), dtype=np.float32)
        all_lats = np.empty((count, verts_per_path), dtype=np.float32)
        all_lons[:, 0] = start_lon
        all_lats[:, 0] = start_lat
        all_lons[:, 1:] = start_lon[:, None] + np.cumsum(step_lon, axis=1)
        all_lats[:, 1:] = start_lat[:, None] + np.cumsum(step_lat, axis=1)

        # Per-path colors
        colors_rgb = rng.integers(30, 256, (count, 3), dtype=np.uint8)

        # --- Build numpy arrays for binary fast path ---
        total_verts = count * verts_per_path

        # Flatten coordinates: (total_verts, 2) float32
        path_coords = np.empty((total_verts, 2), dtype=np.float32)
        path_coords[:, 0] = all_lons.ravel()
        path_coords[:, 1] = all_lats.ravel()

        # Start indices
        start_indices = (np.arange(count, dtype=np.uint32) * verts_per_path)

        # Per-vertex colors: expand per-path to per-vertex
        vertex_colors = np.empty((total_verts, 4), dtype=np.uint8)
        for v in range(verts_per_path):
            vertex_colors[v::verts_per_path, 0] = colors_rgb[:, 0]
            vertex_colors[v::verts_per_path, 1] = colors_rgb[:, 1]
            vertex_colors[v::verts_per_path, 2] = colors_rgb[:, 2]
            vertex_colors[v::verts_per_path, 3] = 180

        arrays = {
            "path_coords": path_coords,
            "start_indices": start_indices,
            "colors": vertex_colors,
        }

        # --- Build list of dicts for JSON mode ---
        paths = []
        for i in range(count):
            path = [[float(all_lons[i, j]), float(all_lats[i, j])] for j in range(verts_per_path)]
            paths.append({
                "path": path,
                "color": [int(colors_rgb[i, 0]), int(colors_rgb[i, 1]), int(colors_rgb[i, 2]), 180],
            })

        return paths, arrays

    return (generate_paths,)


@app.cell
def _(mo):
    path_count_dropdown = mo.ui.dropdown(
        options={"25k": 25_000, "50k": 50_000, "100k": 100_000, "200k": 200_000},
        value="100k",
        label="Path count",
    )
    no_pick_switch = mo.ui.switch(value=True, label="Disable picking")
    const_color_switch = mo.ui.switch(value=False, label="Constant color")

    mo.hstack(
        [path_count_dropdown, no_pick_switch, const_color_switch],
        justify="start",
        gap=2,
    )
    return const_color_switch, no_pick_switch, path_count_dropdown


@app.cell
def _(generate_paths, mo, path_count_dropdown, time):
    count = path_count_dropdown.value
    _t0 = time.perf_counter()
    paths, paths_arrays = generate_paths(count)
    gen_time_ms = (time.perf_counter() - _t0) * 1000

    mo.md(f"Generated **{len(paths):,}** paths in **{gen_time_ms:.0f} ms**")
    return count, gen_time_ms, paths, paths_arrays


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
    const_color_switch,
    dgl,
    json,
    json_map,
    no_pick_switch,
    paths,
    time,
):
    _t0 = time.perf_counter()

    _color = [100, 150, 200, 180] if const_color_switch.value else "color"

    _spec = dgl.PathLayer(
        data=paths,
        get_path="path",
        get_color=_color,
        width_min_pixels=1,
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
    bin_widget = mo.ui.anywidget(bin_map)
    return bin_map, bin_widget


@app.cell
def _(bin_widget):
    bin_widget
    return


@app.cell
def _(
    bin_map,
    const_color_switch,
    count,
    dgl,
    no_pick_switch,
    paths_arrays,
    time,
):
    from deckgl_marimo._binary import pack_binary

    _t0 = time.perf_counter()

    _layer = dgl.PathLayer(
        get_color=[100, 150, 200, 180] if const_color_switch.value else "color",
        width_min_pixels=1,
        pickable=not no_pick_switch.value,
        opacity=0.8,
        use_binary=True,
    )
    _spec = _layer.to_spec()

    # Pack binary data directly from numpy arrays
    _arrays = paths_arrays
    attrs = {
        "getPath": (_arrays["path_coords"], "float32", 2),
    }
    if not const_color_switch.value:
        attrs["getColor"] = (_arrays["colors"], "uint8", 4)
    _meta, _buf = pack_binary(count, attrs, start_indices=_arrays["start_indices"])
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
    ### Comparison — {count:,} paths

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
            "Paths": count,
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
