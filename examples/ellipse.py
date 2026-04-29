# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "pandas",
#     "deckgl-marimo",
# ]
#
# [tool.uv.sources]
# deckgl-marimo = { path = ".." }
# ///

import marimo

__generated_with = "0.19.11"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    import pandas as pd

    return (pd,)


@app.cell
def _():
    import deckgl_marimo as dgl

    return (dgl,)


@app.cell
def _(mo, pd):
    # Sample data: storm cells with elliptical uncertainty regions
    storms = pd.DataFrame(
        [
            {"name": "Cell A", "lon": -90.10, "lat": 29.95, "major": 5000, "minor": 3000, "bearing": 45},
            {"name": "Cell B", "lon": -89.80, "lat": 30.05, "major": 8000, "minor": 4000, "bearing": 120},
            {"name": "Cell C", "lon": -90.30, "lat": 30.10, "major": 6000, "minor": 6000, "bearing": 0},
            {"name": "Cell D", "lon": -89.95, "lat": 29.85, "major": 10000, "minor": 3000, "bearing": 90},
            {"name": "Cell E", "lon": -90.20, "lat": 29.90, "major": 4000, "minor": 2000, "bearing": 160},
        ]
    )
    mo.md(
        f"**EllipseLayer** — **{len(storms)}** storm cells with elliptical uncertainty regions (diameters in meters, 0=north clockwise)"
    )
    return (storms,)


@app.cell
def _(mo):
    show_dots = mo.ui.switch(value=True, label="Show Centers")
    filled = mo.ui.switch(value=True, label="Filled")
    stroked = mo.ui.switch(value=True, label="Stroked")
    mo.hstack([show_dots, filled, stroked], justify="start", gap=2)
    return filled, show_dots, stroked


@app.cell
def _(dgl, mo):
    map_widget = dgl.Map(basemap="dark-matter", center=(-90.05, 29.97), zoom=10)
    widget = map_widget.as_widget()
    return map_widget, widget


@app.cell
def _(widget):
    widget
    return


@app.cell
def _(dgl, filled, map_widget, show_dots, storms, stroked):
    map_widget.layer_specs = [
        spec
        for spec in dgl.EllipseLayer(
            data=storms.to_dict("records"),
            center=["lon", "lat"],
            major_axis="major",
            minor_axis="minor",
            orientation="bearing",
            units="meters",
            show_center_dots=show_dots.value,
            filled=filled.value,
            stroked=stroked.value,
            fill_color=[0, 140, 255, 80],
            line_color=[0, 200, 255, 255],
            line_width=2,
        ).to_specs()
    ]
    return


if __name__ == "__main__":
    app.run()
