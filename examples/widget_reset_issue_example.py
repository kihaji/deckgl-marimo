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

__generated_with = "0.22.0"
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
def _(mo):
    mo.md("""
    # HexagonLayer — single-cell repro of issue #5

    This notebook intentionally reproduces the camera-reset behavior described in
    [issue #5](https://github.com/kihaji/deckgl-marimo/issues/5). Compare it to
    `02_hexagon.py`, which uses the 2-step pattern (Map built in a non-reactive
    cell, `map.layer_specs = [...]` assigned in the reactive cell) and does *not*
    reset the camera.

    **To reproduce:**

    1. Pan and zoom the map away from its initial view.
    2. Move any slider one step.
    3. Observe that the camera snaps back to the constructor defaults
       (`center=(-1.4157, 52.2324)`, `zoom=6.0`, `pitch=40.5`). The viewport
       table at the bottom reflects the reset.

    The reactive cell below builds `dgl.Map(layers=[...]).as_widget()` in a
    single expression, so every slider change constructs a fresh `Map` instance
    with a new anywidget comm — exactly the path described in the issue.
    """)
    return


@app.cell
def _(mo, pd):
    URL = "https://raw.githubusercontent.com/visgl/deck.gl-data/master/examples/3d-heatmap/heatmap-data.csv"
    df = pd.read_csv(URL).rename(columns={"lng": "lon"})
    mo.md(f"**HexagonLayer** — Loaded **{len(df):,}** records")
    return (df,)


@app.cell
def _(mo):
    radius_slider = mo.ui.slider(start=200, stop=5000, step=100, value=1000, show_value=True, label="Radius (m)")
    coverage_slider = mo.ui.slider(start=0.1, stop=1.0, step=0.1, value=1.0, show_value=True, label="Coverage")
    elevation_slider = mo.ui.slider(start=10, stop=500, step=10, value=250, show_value=True, label="Elevation Scale")
    mo.hstack([radius_slider, coverage_slider, elevation_slider], justify="start", gap=2)
    return coverage_slider, elevation_slider, radius_slider


@app.cell
def _(coverage_slider, df, dgl, elevation_slider, radius_slider):
    widget = dgl.Map(
        basemap="dark-matter",
        center=(-1.4157, 52.2324),
        zoom=6.0,
        pitch=40.5,
        layers=[
            dgl.HexagonLayer(
                data=df.to_dict("records"),
                get_position=["lon", "lat"],
                radius=radius_slider.value,
                coverage=coverage_slider.value,
                elevation_scale=elevation_slider.value,
                extruded=True,
                pickable=True,
                gpu_aggregation=False,
            ),
        ],
    ).as_widget()
    widget
    return (widget,)


@app.cell
def _(mo, widget):
    viewport = widget.value.get("viewport", {})

    def _fmt(val, spec):
        return format(val, spec) if isinstance(val, (int, float)) else "—"

    mo.md(
        f"""
    **Viewport**

    | Property | Value |
    |----------|-------|
    | Longitude | {_fmt(viewport.get('longitude'), '.4f')} |
    | Latitude | {_fmt(viewport.get('latitude'), '.4f')} |
    | Zoom | {_fmt(viewport.get('zoom'), '.2f')} |
    | Pitch | {_fmt(viewport.get('pitch'), '.1f')} |
    | Bearing | {_fmt(viewport.get('bearing'), '.1f')} |
    """
    )
    return


if __name__ == "__main__":
    app.run()
