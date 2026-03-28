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
    URL = "https://raw.githubusercontent.com/visgl/deck.gl-data/master/examples/3d-heatmap/heatmap-data.csv"
    df = pd.read_csv(URL)
    mo.md(f"**HeatmapLayer** — Loaded **{len(df):,}** records")
    return (df,)


@app.cell
def _(mo):
    radius_slider = mo.ui.slider(
        start=5, stop=100, step=5, value=30, show_value=True, label="Radius (px)"
    )
    intensity_slider = mo.ui.slider(
        start=0.1, stop=5.0, step=0.1, value=1.0, show_value=True, label="Intensity"
    )
    threshold_slider = mo.ui.slider(
        start=0.0, stop=1.0, step=0.05, value=0.05, show_value=True, label="Threshold"
    )
    mo.hstack([radius_slider, intensity_slider, threshold_slider], justify="start", gap=2)
    return intensity_slider, radius_slider, threshold_slider


@app.cell
def _(dgl, df, intensity_slider, mo, radius_slider, threshold_slider):
    widget = mo.ui.anywidget(
        dgl.Map(
            layers=[
                dgl.HeatmapLayer(
                    data=df.to_dict("records"),
                    get_position=["lng", "lat"],
                    radius_pixels=radius_slider.value,
                    intensity=intensity_slider.value,
                    threshold=threshold_slider.value,
                ),
            ],
            basemap="dark-matter",
            center=(-1.4157, 52.2324),
            zoom=6.0,
        )
    )
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
"""
    )
    return (viewport,)


if __name__ == "__main__":
    app.run()
