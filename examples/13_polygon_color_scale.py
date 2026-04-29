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

    return (np,)


@app.cell
def _(np):
    def generate_polygons(count, seed=42):
        """Generate a grid of small non-overlapping pentagons.

        Each row has:
        - "polygon": closed ring of [lon, lat] pairs
        - "value":   skewed (exponential) magnitude — good for log color scale
        - "category": 0..4, used by the custom color function demo
        """
        rng = np.random.default_rng(seed)

        cols = int(np.ceil(np.sqrt(count)))
        rows = int(np.ceil(count / cols))
        total_cells = cols * rows

        lon_range, lat_range = 40.0, 25.0
        lon0, lat0 = -20.0, 30.0
        cell_w, cell_h = lon_range / cols, lat_range / rows
        radius = min(cell_w, cell_h) * 0.4

        col_idx = np.arange(total_cells) % cols
        row_idx = np.arange(total_cells) // cols
        cx = lon0 + (col_idx + 0.5) * cell_w
        cy = lat0 + (row_idx + 0.5) * cell_h
        cx, cy = cx[:count], cy[:count]

        n_verts = 5
        base_angles = np.linspace(0, 2 * np.pi, n_verts, endpoint=False)
        jitter = rng.uniform(-0.1, 0.1, (count, n_verts))
        angles = base_angles[None, :] + jitter
        r = radius * (0.8 + rng.uniform(0, 0.3, (count, n_verts)))

        vx = cx[:, None] + r * np.cos(angles)
        vy = cy[:, None] + r * np.sin(angles)

        # Exponential values — a linear color ramp would wash these out;
        # a log scale brings out the structure.
        values = rng.exponential(scale=1.0, size=count)
        categories = rng.integers(0, 5, size=count)

        polygons = []
        for i in range(count):
            ring = [[float(vx[i, j]), float(vy[i, j])] for j in range(n_verts)]
            ring.append(ring[0])  # close ring
            polygons.append(
                {
                    "polygon": ring,
                    "value": float(values[i]),
                    "category": int(categories[i]),
                }
            )
        return polygons

    polygons = generate_polygons(20_000)
    return (polygons,)


@app.cell
def _(mo, polygons):
    mo.md(f"""
    **PolygonLayer + ColorScale** — {len(polygons):,} polygons, "
        f"binary packed (`use_binary=True`)
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ### 1. Logarithmic ColorScale

    `get_fill_color=dgl.ColorScale("value", palette="viridis", scale="log")`.
    The `value` column is drawn from an exponential distribution — a linear scale
    would flatten most polygons into the same color, while `scale="log"` reveals
    the full range of magnitudes.
    """)
    return


@app.cell
def _(dgl, mo, polygons):
    layer1 = dgl.PolygonLayer(
        data=polygons,
        get_polygon="polygon",
        get_fill_color=dgl.ColorScale(
            "value", palette="viridis", scale="log"
        ),
        stroked=False,
        filled=True,
        opacity=0.85,
        use_binary=True,
    )
    map1 = dgl.Map(
        layers=[layer1],
        basemap="dark-matter",
        center=(0.0, 42.0),
        zoom=4,
    )
    widget1 = map1.as_widget()
    return (widget1,)


@app.cell
def _(widget1):
    widget1
    return


@app.cell
def _(mo):
    mo.md("""
    ### 2. Custom color function

    `get_fill_color=lambda row: [...]` — a plain Python callable receives each
    row and returns an `[R, G, B, A]` list. Here `category` picks a hue and
    `value` drives the brightness, all routed through the binary fast path.
    """)
    return


@app.cell
def _(dgl, mo, polygons):
    # Five distinct base hues, one per category.
    category_hues = [
        (220, 60, 60),    # red
        (60, 180, 75),    # green
        (60, 130, 240),   # blue
        (240, 180, 50),   # amber
        (170, 80, 220),   # purple
    ]

    def fill_from_row(row):
        r, g, b = category_hues[row["category"]]
        # Map value (roughly 0..5 for an exponential(1) draw) to a 0.4..1.0
        # brightness multiplier so differences stay visible.
        v = row["value"]
        t = min(1.0, v / 4.0)
        k = 0.4 + 0.6 * t
        return [int(r * k), int(g * k), int(b * k), 210]

    layer2 = dgl.PolygonLayer(
        data=polygons,
        get_polygon="polygon",
        get_fill_color=fill_from_row,
        stroked=False,
        filled=True,
        opacity=0.9,
        use_binary=True,
    )
    map2 = dgl.Map(
        layers=[layer2],
        basemap="dark-matter",
        center=(0.0, 42.0),
        zoom=4,
    )
    widget2 = map2.as_widget()
    return (widget2,)


@app.cell
def _(widget2):
    widget2
    return


if __name__ == "__main__":
    app.run()
