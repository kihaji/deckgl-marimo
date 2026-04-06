# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "deckgl-marimo",
#     "numpy",
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
    from deckgl_marimo._binary import pack_polygon_binary

    return dgl, pack_polygon_binary


@app.cell
def _():
    import numpy as np
    import time
    import pathlib

    return np, pathlib, time


@app.cell
def _(mo, np, pathlib, time):
    _t0 = time.perf_counter()
    _path = pathlib.Path(__file__).parent / "data" / "polygons_1m.npz"
    npz = np.load(_path)
    coords = npz["coords"]
    start_indices = npz["start_indices"]
    vertex_colors = npz["vertex_colors"]
    load_ms = (time.perf_counter() - _t0) * 1000

    n_polygons = len(start_indices)
    n_verts = len(coords)
    mem_mb = (coords.nbytes + start_indices.nbytes + vertex_colors.nbytes) / 1024 / 1024

    mo.md(f"""
    ### Loaded **{n_polygons:,}** polygons ({n_verts:,} vertices) in **{load_ms:.0f} ms**
    Memory: {mem_mb:.1f} MB ({coords.dtype} coords, {vertex_colors.dtype} colors)
    """)
    return coords, load_ms, n_polygons, start_indices, vertex_colors


@app.cell
def _(mo):
    no_pick_switch = mo.ui.switch(value=True, label="Disable picking")
    const_color_switch = mo.ui.switch(value=False, label="Constant color")

    mo.hstack(
        [no_pick_switch, const_color_switch],
        justify="start",
        gap=2,
    )
    return const_color_switch, no_pick_switch


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
    coords,
    dgl,
    map_widget,
    no_pick_switch,
    pack_polygon_binary,
    start_indices,
    time,
    vertex_colors,
):
    _t0 = time.perf_counter()

    _fill = [100, 150, 200, 180] if const_color_switch.value else "color"

    _layer = dgl.PolygonLayer(
        get_fill_color=_fill,
        get_line_color=[255, 255, 255, 100],
        get_line_width=1,
        filled=True,
        stroked=False,
        pickable=not no_pick_switch.value,
        opacity=0.8,
        use_binary=True,
    )
    _spec = _layer.to_spec()

    _arrays = {
        "polygon_coords": coords,
        "start_indices": start_indices,
        "colors": None if const_color_switch.value else vertex_colors,
    }
    _meta, _buf = pack_polygon_binary(_arrays)
    _meta["id"] = _spec["id"]

    map_widget.binary_metadata = {"layers": [_meta]}
    map_widget.binary_data = _buf
    map_widget.layer_specs = [_spec]

    _t1 = time.perf_counter()
    ser_ms = (_t1 - _t0) * 1000
    payload_bytes = len(_buf)
    return payload_bytes, ser_ms


@app.cell
def _(load_ms, mo, n_polygons, payload_bytes, ser_ms, widget):
    perf = widget.value.get("perf_metrics", {})
    fps = perf.get("fps", "—")
    ft_avg = perf.get("frameTimeAvg", "—")
    ft_min = perf.get("frameTimeMin", "—")
    ft_max = perf.get("frameTimeMax", "—")

    payload_mb = payload_bytes / (1024 * 1024)

    mo.md(f"""
    ### 1M Polygon Stress Test — Binary Path

    | Metric | Value |
    |--------|-------|
    | **Polygons** | {n_polygons:,} |
    | **File load** | {load_ms:.0f} ms |
    | **Binary packing** | {ser_ms:.0f} ms |
    | **Payload** | {payload_mb:.1f} MB |
    | **FPS** | {fps} |
    | **Frame time (avg)** | {ft_avg} ms |
    | **Frame time (min/max)** | {ft_min} / {ft_max} ms |
    """)
    return


@app.cell
def _(
    const_color_switch,
    mo,
    n_polygons,
    no_pick_switch,
    payload_bytes,
    ser_ms,
    set_history,
    widget,
):
    def _snapshot():
        perf = widget.value.get("perf_metrics", {})
        row = {
            "Polygons": n_polygons,
            "Pack (ms)": round(ser_ms, 1),
            "Payload (MB)": round(payload_bytes / (1024 * 1024), 1),
            "FPS": perf.get("fps", "—"),
            "Frame Time (ms)": perf.get("frameTimeAvg", "—"),
            "Picking off": no_pick_switch.value,
            "Const color": const_color_switch.value,
        }
        set_history(lambda h: h + [row])

    snapshot_button = mo.ui.button(label="Capture snapshot", on_click=lambda _: _snapshot())
    snapshot_button
    return (snapshot_button,)


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
    return (pd,)


if __name__ == "__main__":
    app.run()
