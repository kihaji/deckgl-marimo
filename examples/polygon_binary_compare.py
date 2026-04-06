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

__generated_with = "0.22.4"
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
    def generate_polygons_fast(count, seed=42):
        """Generate non-overlapping polygons using numpy.

        Returns (polygons_list, polygons_arrays) where:
        - polygons_list: list of dicts for JSON mode
        - polygons_arrays: dict of numpy arrays for binary fast path
        """
        rng = np.random.default_rng(seed)

        cols = int(np.ceil(np.sqrt(count)))
        rows = int(np.ceil(count / cols))
        total_cells = cols * rows

        lon_range, lat_range = 320.0, 110.0
        cell_w, cell_h = lon_range / cols, lat_range / rows
        radius = min(cell_w, cell_h) * 0.3

        col_idx = np.arange(total_cells) % cols
        row_idx = np.arange(total_cells) // cols
        cx = -160.0 + (col_idx + 0.5) * cell_w + rng.uniform(-cell_w * 0.1, cell_w * 0.1, total_cells)
        cy = -55.0 + (row_idx + 0.5) * cell_h + rng.uniform(-cell_h * 0.1, cell_h * 0.1, total_cells)
        cx, cy = cx[:count], cy[:count]

        n_verts = 5
        angles = rng.uniform(0, 2 * np.pi, (count, n_verts))
        angles.sort(axis=1)
        radii = radius + rng.uniform(-radius * 0.5, radius * 0.5, (count, n_verts))

        vx = cx[:, None] + radii * np.cos(angles)
        vy = cy[:, None] + radii * np.sin(angles)

        # Per-polygon colors (count, 3)
        colors_rgb = rng.integers(30, 256, (count, 3), dtype=np.uint8)

        # --- Build numpy arrays for binary fast path ---
        # Each polygon has n_verts + 1 vertices (closed ring)
        verts_per_poly = n_verts + 1
        total_verts = count * verts_per_poly

        # Coordinates: (total_verts, 2) float32
        coords = np.empty((total_verts, 2), dtype=np.float32)
        for v in range(n_verts):
            coords[v::verts_per_poly, 0] = vx[:, v].astype(np.float32)
            coords[v::verts_per_poly, 1] = vy[:, v].astype(np.float32)
        # Close the ring: last vertex = first vertex
        coords[n_verts::verts_per_poly, 0] = vx[:, 0].astype(np.float32)
        coords[n_verts::verts_per_poly, 1] = vy[:, 0].astype(np.float32)

        # Start indices
        start_indices = np.arange(count, dtype=np.uint32) * verts_per_poly

        # Per-vertex colors: expand per-polygon to per-vertex
        vertex_colors = np.empty((total_verts, 4), dtype=np.uint8)
        for v in range(verts_per_poly):
            vertex_colors[v::verts_per_poly, 0] = colors_rgb[:, 0]
            vertex_colors[v::verts_per_poly, 1] = colors_rgb[:, 1]
            vertex_colors[v::verts_per_poly, 2] = colors_rgb[:, 2]
            vertex_colors[v::verts_per_poly, 3] = 180

        arrays = {
            "polygon_coords": coords,
            "start_indices": start_indices,
            "colors": vertex_colors,
        }

        # --- Build list of dicts for JSON mode ---
        polygons = []
        for i in range(count):
            ring = [[float(vx[i, j]), float(vy[i, j])] for j in range(n_verts)]
            ring.append(ring[0])
            polygons.append({
                "polygon": ring,
                "color": [int(colors_rgb[i, 0]), int(colors_rgb[i, 1]), int(colors_rgb[i, 2]), 180],
                "value": float(rng.random()),
            })

        return polygons, arrays

    return (generate_polygons_fast,)


@app.cell
def _(mo):
    polygon_count_dropdown = mo.ui.dropdown(
        options={"50k": 50_000, "100k": 100_000, "200k": 200_000, "300k": 300_000},
        value="200k",
        label="Polygon count",
    )
    no_pick_switch = mo.ui.switch(value=True, label="Disable picking")
    no_stroke_switch = mo.ui.switch(value=True, label="Disable strokes")
    const_color_switch = mo.ui.switch(value=False, label="Constant color")

    mo.hstack(
        [polygon_count_dropdown, no_pick_switch, no_stroke_switch, const_color_switch],
        justify="start",
        gap=2,
    )
    return (
        const_color_switch,
        no_pick_switch,
        no_stroke_switch,
        polygon_count_dropdown,
    )


@app.cell
def _(generate_polygons_fast, mo, polygon_count_dropdown, time):
    count = polygon_count_dropdown.value
    _t0 = time.perf_counter()
    polygons, polygon_arrays = generate_polygons_fast(count)
    gen_time_ms = (time.perf_counter() - _t0) * 1000

    mo.md(f"Generated **{len(polygons):,}** polygons in **{gen_time_ms:.0f} ms**")
    return count, gen_time_ms, polygon_arrays, polygons


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
    no_stroke_switch,
    polygons,
    time,
):
    _t0 = time.perf_counter()

    _fill = [100, 150, 200, 180] if const_color_switch.value else "color"

    _spec = dgl.PolygonLayer(
        data=polygons,
        get_polygon="polygon",
        get_fill_color=_fill,
        get_line_color=[255, 255, 255, 100],
        get_line_width=1,
        filled=True,
        stroked=not no_stroke_switch.value,
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
    dgl,
    no_pick_switch,
    no_stroke_switch,
    polygon_arrays,
    time,
):
    from deckgl_marimo._binary import pack_polygon_binary

    _t0 = time.perf_counter()

    _fill = [100, 150, 200, 180] if const_color_switch.value else "color"

    # Create layer for its spec (non-data props like opacity, stroked, etc.)
    _layer = dgl.PolygonLayer(
        get_fill_color=_fill,
        get_line_color=[255, 255, 255, 100],
        get_line_width=1,
        filled=True,
        stroked=not no_stroke_switch.value,
        pickable=not no_pick_switch.value,
        opacity=0.8,
        use_binary=True,
    )
    _spec = _layer.to_spec()

    # Pack binary data directly from numpy arrays (fast path)
    _arrays = polygon_arrays
    if const_color_switch.value:
        _arrays = {**polygon_arrays, "colors": None}
    _meta, _buf = pack_polygon_binary(_arrays)
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
    ### Comparison — {count:,} polygons

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
    no_stroke_switch,
    set_history,
):
    def _snapshot():
        jp = json_widget.value.get("perf_metrics", {})
        bp = bin_widget.value.get("perf_metrics", {})
        row = {
            "Polygons": count,
            "JSON Ser (ms)": round(json_ser_ms, 1),
            "Bin Ser (ms)": round(bin_ser_ms, 1),
            "JSON Size (MB)": round(json_payload_bytes / (1024 * 1024), 1),
            "Bin Size (MB)": round(bin_payload_bytes / (1024 * 1024), 1),
            "JSON FPS": jp.get("fps", "—"),
            "Bin FPS": bp.get("fps", "—"),
            "Picking off": no_pick_switch.value,
            "Strokes off": no_stroke_switch.value,
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
