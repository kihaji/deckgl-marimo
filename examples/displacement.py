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
    # Simulated vessel displacement data: recorded position vs reported (AIS) position
    vessels = pd.DataFrame(
        [
            {"name": "Vessel A", "rec_lon": -90.10, "rec_lat": 29.95, "rep_lon": -90.07, "rep_lat": 29.97},
            {"name": "Vessel B", "rec_lon": -89.95, "rec_lat": 30.00, "rep_lon": -89.90, "rep_lat": 29.96},
            {"name": "Vessel C", "rec_lon": -90.20, "rec_lat": 29.90, "rep_lon": -90.25, "rep_lat": 29.88},
            {"name": "Vessel D", "rec_lon": -89.80, "rec_lat": 30.05, "rep_lon": -89.82, "rep_lat": 30.10},
            {"name": "Vessel E", "rec_lon": -90.05, "rec_lat": 29.85, "rep_lon": -90.00, "rep_lat": 29.80},
            {"name": "Vessel F", "rec_lon": -90.30, "rec_lat": 30.10, "rep_lon": -90.35, "rep_lat": 30.15},
            {"name": "Vessel G", "rec_lon": -89.70, "rec_lat": 29.92, "rep_lon": -89.65, "rep_lat": 29.95},
            {"name": "Vessel H", "rec_lon": -90.15, "rec_lat": 30.02, "rep_lon": -90.12, "rep_lat": 30.06},
        ]
    )
    mo.md(
        f"**DisplacementLayer** — **{len(vessels)}** vessels showing recorded vs reported positions"
    )
    return (vessels,)


@app.cell
def _(mo):
    show_arcs = mo.ui.switch(value=True, label="Show Arcs")
    show_origin = mo.ui.switch(value=True, label="Show Recorded (green)")
    show_displaced = mo.ui.switch(value=True, label="Show Reported (red)")
    mo.hstack([show_arcs, show_origin, show_displaced], justify="start", gap=2)
    return show_arcs, show_displaced, show_origin


@app.cell
def _(dgl, mo):
    map_widget = dgl.Map(basemap="dark-matter", center=(-90.0, 29.95), zoom=10)
    widget = mo.ui.anywidget(map_widget)
    return map_widget, widget


@app.cell
def _(widget):
    widget
    return


@app.cell
def _(dgl, map_widget, show_arcs, show_displaced, show_origin, vessels):
    map_widget.layer_specs = [
        spec
        for spec in dgl.DisplacementLayer(
            data=vessels.to_dict("records"),
            origin=["rec_lon", "rec_lat"],
            displaced=["rep_lon", "rep_lat"],
            show_arcs=show_arcs.value,
            show_origin_dots=show_origin.value,
            show_displaced_dots=show_displaced.value,
            arc_width=2,
        ).to_specs()
    ]
    return


if __name__ == "__main__":
    app.run()
