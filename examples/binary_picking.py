# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "deckgl-marimo",
#     "numpy",
# ]
#
# [tool.uv.sources]
# deckgl-marimo = { path = ".." }
# ///

"""Binary-packed PolygonLayer with picking enabled.

Demonstrates that click/hover events work on binary layers. Because the
layer is passed to ``Map(layers=[...])`` in the normal way, the Python-side
observer on the Map will resolve ``click_info["object"]`` back to the
original row for us — no manual index lookup needed.
"""

import marimo

__generated_with = "0.22.4"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import deckgl_marimo as dgl

    return dgl, mo, np


@app.cell
def _(mo):
    count_dropdown = mo.ui.dropdown(
        options={"1k": 1_000, "5k": 5_000, "20k": 20_000, "50k": 50_000},
        value="5k",
        label="Polygon count",
    )
    count_dropdown
    return (count_dropdown,)


@app.cell
def _(count_dropdown, np):
    count = count_dropdown.value
    rng = np.random.default_rng(0)

    cols = int(np.ceil(np.sqrt(count)))
    rows = int(np.ceil(count / cols))
    lon_range, lat_range = 320.0, 110.0
    cell_w, cell_h = lon_range / cols, lat_range / rows
    radius = min(cell_w, cell_h) * 0.35

    col_idx = np.arange(cols * rows) % cols
    row_idx = np.arange(cols * rows) // cols
    cx = -160.0 + (col_idx + 0.5) * cell_w
    cy = -55.0 + (row_idx + 0.5) * cell_h
    cx, cy = cx[:count], cy[:count]

    n_verts = 5
    angles = rng.uniform(0, 2 * np.pi, (count, n_verts))
    angles.sort(axis=1)
    radii = radius + rng.uniform(-radius * 0.4, radius * 0.4, (count, n_verts))
    vx = cx[:, None] + radii * np.cos(angles)
    vy = cy[:, None] + radii * np.sin(angles)

    colors = rng.integers(40, 256, (count, 3), dtype=int).tolist()

    polygons = []
    for i in range(count):
        ring = [[float(vx[i, j]), float(vy[i, j])] for j in range(n_verts)]
        ring.append(ring[0])
        polygons.append({
            "id": i,
            "polygon": ring,
            "color": [colors[i][0], colors[i][1], colors[i][2], 180],
            "value": float(rng.random()),
            "tooltip": f"Polygon #{i} (value={rng.random():.2f})",
        })
    return (polygons,)


@app.cell
def _(dgl, mo, polygons):
    layer = dgl.PolygonLayer(
        data=polygons,
        get_polygon="polygon",
        get_fill_color="color",
        get_line_color=[255, 255, 255, 120],
        get_line_width=1,
        filled=True,
        stroked=True,
        opacity=0.8,
        pickable=True,
        auto_highlight=True,
        use_binary=True,
    )
    binary_map = dgl.Map(
        layers=[layer],
        basemap="dark-matter",
        center=(0, 0),
        zoom=1,
        height="500px",
    )
    widget = mo.ui.anywidget(binary_map)
    widget
    return (widget,)


@app.cell
def _(mo, widget):
    click = widget.value.get("click_info", {})
    hover = widget.value.get("hover_info", {})

    def _fmt(title, info):
        if not info:
            return f"**{title}**\n\n_nothing yet — interact with the map_"
        obj = info.get("object") or {}
        return (
            f"**{title}**\n\n"
            f"- layer: `{info.get('layer_id')}`\n"
            f"- index: `{info.get('index')}`\n"
            f"- coordinate: `{info.get('coordinate')}`\n"
            f"- row id: `{obj.get('id')}`\n"
            f"- row value: `{obj.get('value')}`\n"
        )

    mo.hstack(
        [mo.md(_fmt("Click", click)), mo.md(_fmt("Hover", hover))],
        justify="start",
        gap=2,
    )
    return


if __name__ == "__main__":
    app.run()
