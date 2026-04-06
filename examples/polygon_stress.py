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
        """Generate non-overlapping polygons using numpy for speed.

        Grid-based placement across lon [-160, 160] and lat [-55, 55].
        Each polygon is a random 5-sided shape at its grid cell center.
        """
        rng = np.random.default_rng(seed)

        cols = int(np.ceil(np.sqrt(count)))
        rows = int(np.ceil(count / cols))
        total_cells = cols * rows

        lon_range = 320.0  # -160 to 160
        lat_range = 110.0  # -55 to 55
        cell_w = lon_range / cols
        cell_h = lat_range / rows
        radius = min(cell_w, cell_h) * 0.3

        # Grid cell centers for all cells, then take first `count`
        col_idx = np.arange(total_cells) % cols
        row_idx = np.arange(total_cells) // cols
        cx = -160.0 + (col_idx + 0.5) * cell_w + rng.uniform(-cell_w * 0.1, cell_w * 0.1, total_cells)
        cy = -55.0 + (row_idx + 0.5) * cell_h + rng.uniform(-cell_h * 0.1, cell_h * 0.1, total_cells)
        cx = cx[:count]
        cy = cy[:count]

        # Fixed 5 vertices per polygon for vectorized generation
        n_verts = 5
        # Random angles, sorted per polygon
        angles = rng.uniform(0, 2 * np.pi, (count, n_verts))
        angles.sort(axis=1)

        # Random radii
        radii = radius + rng.uniform(-radius * 0.5, radius * 0.5, (count, n_verts))

        # Compute vertex positions: (count, n_verts, 2)
        vx = cx[:, None] + radii * np.cos(angles)
        vy = cy[:, None] + radii * np.sin(angles)

        # Random colors
        colors = rng.integers(30, 256, (count, 3))

        # Build list of dicts (the serialization bottleneck we're measuring)
        polygons = []
        for i in range(count):
            ring = [[float(vx[i, j]), float(vy[i, j])] for j in range(n_verts)]
            ring.append(ring[0])  # close ring
            polygons.append({
                "polygon": ring,
                "color": [int(colors[i, 0]), int(colors[i, 1]), int(colors[i, 2]), 180],
                "value": float(rng.random()),
            })

        return polygons

    return (generate_polygons_fast,)


@app.cell
def _(generate_polygons_fast, mo, time):
    _t0 = time.perf_counter()
    polygons_200k = generate_polygons_fast(200_000)
    gen_time_ms = (time.perf_counter() - _t0) * 1000

    mo.md(f"Generated **{len(polygons_200k):,}** polygons in **{gen_time_ms:.0f} ms**")
    get_history, set_history = mo.state([])
    return gen_time_ms, get_history, polygons_200k, set_history


@app.cell
def _(mo):
    no_pick_switch = mo.ui.switch(value=True, label="Disable picking")
    no_stroke_switch = mo.ui.switch(value=True, label="Disable strokes")
    const_color_switch = mo.ui.switch(value=False, label="Constant color")

    mo.hstack(
        [no_pick_switch, no_stroke_switch, const_color_switch],
        justify="start",
        gap=2,
    )
    return const_color_switch, no_pick_switch, no_stroke_switch


@app.cell
def _(dgl, mo):
    map_widget = dgl.Map(
        basemap="dark-matter",
        center=(0, 0),
        zoom=1,
        height="700px",
    )
    widget = mo.ui.anywidget(map_widget)
    return map_widget, widget


@app.cell
def _(widget):
    widget
    return


@app.cell
def _(
    const_color_switch,
    dgl,
    json,
    map_widget,
    no_pick_switch,
    no_stroke_switch,
    polygons_200k,
    time,
):
    _t0 = time.perf_counter()

    fill_color = [100, 150, 200, 180] if const_color_switch.value else "color"

    layer_spec = dgl.PolygonLayer(
        data=polygons_200k,
        get_polygon="polygon",
        get_fill_color=fill_color,
        get_line_color=[255, 255, 255, 100],
        get_line_width=1,
        filled=True,
        stroked=not no_stroke_switch.value,
        pickable=not no_pick_switch.value,
        opacity=0.8,
    ).to_spec()

    specs = [layer_spec]
    map_widget.layer_specs = specs

    t1 = time.perf_counter()
    serialization_ms = (t1 - _t0) * 1000
    payload_bytes = len(json.dumps(specs).encode("utf-8"))
    polygon_count = len(polygons_200k)
    return payload_bytes, polygon_count, serialization_ms


@app.cell
def _(gen_time_ms, mo, payload_bytes, polygon_count, serialization_ms, widget):
    perf = widget.value.get("perf_metrics", {})
    fps = perf.get("fps", "—")
    ft_avg = perf.get("frameTimeAvg", "—")
    ft_min = perf.get("frameTimeMin", "—")
    ft_max = perf.get("frameTimeMax", "—")

    if payload_bytes < 1024 * 1024:
        payload_display = f"{payload_bytes / 1024:.1f} KB"
    else:
        payload_display = f"{payload_bytes / (1024 * 1024):.1f} MB"

    mo.md(f"""
    ### 200k Polygon Stress Test

    | Metric | Value |
    |--------|-------|
    | **Polygons** | {polygon_count:,} |
    | **FPS** | {fps} |
    | **Frame time (avg)** | {ft_avg} ms |
    | **Frame time (min/max)** | {ft_min} / {ft_max} ms |
    | **Data generation** | {gen_time_ms:.0f} ms |
    | **Python serialization** | {serialization_ms:.0f} ms |
    | **JSON payload** | {payload_display} |
    """)
    return


@app.cell
def _(
    const_color_switch,
    mo,
    no_pick_switch,
    no_stroke_switch,
    payload_bytes,
    polygon_count,
    serialization_ms,
    set_history,
    widget,
):
    def _snapshot():
        perf = widget.value.get("perf_metrics", {})
        row = {
            "Polygons": polygon_count,
            "FPS": perf.get("fps", "—"),
            "Frame Time (ms)": perf.get("frameTimeAvg", "—"),
            "Serialization (ms)": round(serialization_ms, 1),
            "Payload (MB)": round(payload_bytes / (1024 * 1024), 1),
            "Picking off": no_pick_switch.value,
            "Strokes off": no_stroke_switch.value,
            "Const color": const_color_switch.value,
        }
        set_history(lambda h: h + [row])

    snapshot_button = mo.ui.button(label="Capture snapshot", on_click=lambda _: _snapshot())
    snapshot_button
    return


@app.cell
def _(get_history, mo):
    import pandas as pd

    history = get_history()
    if history:
        df = pd.DataFrame(history)
        _history_output = mo.vstack([
            mo.md("### Benchmark History"),
            mo.ui.table(df),
        ])
    else:
        _history_output = mo.md("*Click 'Capture snapshot' to record the current metrics.*")
    _history_output
    return


if __name__ == "__main__":
    app.run()
