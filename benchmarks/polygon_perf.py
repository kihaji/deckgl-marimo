# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "deckgl-marimo",
#     "pandas",
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
    import random
    import time
    import json
    import math

    return json, math, random, time


@app.cell
def _(math, random):
    def generate_polygons(count, offset=0, seed=None):
        """Generate non-overlapping polygons on a global grid.

        Each polygon is a small irregular shape placed at a grid cell center
        with jitter, spread across lon [-160, 160] and lat [-55, 55].
        """
        if seed is not None:
            random.seed(seed)

        cols = math.ceil(math.sqrt(count))
        rows = math.ceil(count / cols)

        lon_range = 320  # -160 to 160
        lat_range = 110  # -55 to 55
        cell_w = lon_range / cols
        cell_h = lat_range / rows
        radius = min(cell_w, cell_h) * 0.3  # polygon radius relative to cell

        polygons = []
        idx = 0
        for row in range(rows):
            for col in range(cols):
                if idx >= count:
                    break
                # Cell center with jitter
                cx = -160 + (col + 0.5) * cell_w + random.uniform(-cell_w * 0.1, cell_w * 0.1)
                cy = -55 + (row + 0.5) * cell_h + random.uniform(-cell_h * 0.1, cell_h * 0.1)

                # Random irregular polygon (4-7 vertices)
                n_verts = random.randint(4, 7)
                angles = sorted(random.uniform(0, 2 * math.pi) for _ in range(n_verts))
                r_variation = radius * 0.5
                ring = []
                for a in angles:
                    r = radius + random.uniform(-r_variation, r_variation)
                    ring.append([cx + r * math.cos(a), cy + r * math.sin(a)])
                ring.append(ring[0])  # close the ring

                polygons.append({
                    "polygon": ring,
                    "color": [
                        random.randint(30, 255),
                        random.randint(30, 255),
                        random.randint(30, 255),
                        180,
                    ],
                    "value": random.random() * 100,
                    "id": offset + idx,
                })
                idx += 1

        return polygons

    return (generate_polygons,)


@app.cell
def _(generate_polygons, mo):
    initial_polygons = generate_polygons(10000, seed=42)
    get_polygons, set_polygons = mo.state(initial_polygons)
    get_history, set_history = mo.state([])
    return get_history, get_polygons, set_history, set_polygons


@app.cell
def _(generate_polygons, mo, set_polygons):
    def _add_10k():
        set_polygons(lambda current: current + generate_polygons(10000, offset=len(current)))

    add_button = mo.ui.button(label="Add 10k polygons", on_click=lambda _: _add_10k())
    no_pick_switch = mo.ui.switch(value=True, label="Disable picking")
    no_stroke_switch = mo.ui.switch(value=False, label="Disable strokes")
    const_color_switch = mo.ui.switch(value=False, label="Constant color")

    mo.hstack(
        [add_button, no_pick_switch, no_stroke_switch, const_color_switch],
        justify="start",
        gap=2,
    )
    return (
        const_color_switch,
        no_pick_switch,
        no_stroke_switch,
    )


@app.cell
def _(get_polygons, mo):
    mo.md(f"""
    ### PolygonLayer Performance Test — **{len(get_polygons()):,}** polygons
    """)
    return


@app.cell
def _(dgl, mo):
    map_widget = dgl.Map(
        basemap="dark-matter",
        center=(0, 0),
        zoom=1,
        height="700px",
    )
    widget = map_widget.as_widget()
    return map_widget, widget


@app.cell
def _(widget):
    widget
    return


@app.cell
def _(
    const_color_switch,
    dgl,
    get_polygons,
    json,
    map_widget,
    no_pick_switch,
    no_stroke_switch,
    time,
):
    polygons = get_polygons()
    polygon_count = len(polygons)

    t0 = time.perf_counter()

    fill_color = [100, 150, 200, 180] if const_color_switch.value else "color"

    layer_spec = dgl.PolygonLayer(
        data=polygons,
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
    serialization_ms = (t1 - t0) * 1000
    payload_bytes = len(json.dumps(specs).encode("utf-8"))
    return payload_bytes, polygon_count, serialization_ms


@app.cell
def _(mo, payload_bytes, polygon_count, serialization_ms, widget):
    perf = widget.value.get("perf_metrics", {})
    fps = perf.get("fps", "—")
    ft_avg = perf.get("frameTimeAvg", "—")
    ft_min = perf.get("frameTimeMin", "—")
    ft_max = perf.get("frameTimeMax", "—")

    payload_display = (
        f"{payload_bytes / 1024:.1f} KB"
        if payload_bytes < 1024 * 1024
        else f"{payload_bytes / (1024 * 1024):.2f} MB"
    )

    mo.md(f"""
    ### Performance Metrics

    | Metric | Value |
    |--------|-------|
    | **Polygons** | {polygon_count:,} |
    | **FPS** | {fps} |
    | **Frame time (avg)** | {ft_avg} ms |
    | **Frame time (min/max)** | {ft_min} / {ft_max} ms |
    | **Python serialization** | {serialization_ms:.1f} ms |
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
            "Payload (KB)": round(payload_bytes / 1024, 1),
            "Picking off": no_pick_switch.value,
            "Strokes off": no_stroke_switch.value,
            "Const color": const_color_switch.value,
        }
        set_history(lambda h: h + [row])

    snapshot_button = mo.ui.button(label="Capture snapshot", on_click=lambda _: _snapshot())
    snapshot_button
    return (snapshot_button,)


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
    return (pd,)


@app.cell
def _(mo):
    mo.md("""
    ---

    ### Optimization Guide

    | Toggle | What it does | Expected impact |
    |--------|-------------|-----------------|
    | **Disable picking** | Sets `pickable: false`, skips color-picking render pass | ~2x FPS for dense layers |
    | **Disable strokes** | Sets `stroked: false`, reduces tessellation + draw calls | Moderate FPS improvement |
    | **Constant color** | Uses single `[r,g,b,a]` instead of per-polygon accessor | GPU batches more efficiently |
    | **Pure deck.gl** | No MapLibre tile rendering, standalone Deck instance | Isolates basemap overhead |

    ### Future Optimizations (not yet implemented)
    - **Binary data / typed arrays**: Bypass JSON serialization, supply pre-built GPU buffers
    - **Data chunking**: Multiple layers per chunk instead of one giant layer
    - **Web worker offloading**: Move data prep off the main thread
    """)
    return


if __name__ == "__main__":
    app.run()
