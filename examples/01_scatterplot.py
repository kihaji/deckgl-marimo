# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pandas",
#     "deckgl-marimo",
#     "marimo",
# ]
#
# [tool.uv.sources]
# deckgl-marimo = { path = ".." }
# ///

import marimo

__generated_with = "0.21.1"
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
    URL = "https://raw.githubusercontent.com/visgl/deck.gl-data/master/examples/line/airports.json"
    _raw = pd.read_json(URL)
    df = _raw.assign(
        lon=_raw["coordinates"].apply(lambda c: c[0]),
        lat=_raw["coordinates"].apply(lambda c: c[1]),
    )
    mo.md(f"**ScatterplotLayer** — Loaded **{len(df):,}** airports")
    return (df,)


@app.cell
def _(mo):
    radius_slider = mo.ui.slider(
        start=1, stop=20, step=1, value=5, show_value=True, label="Radius Scale"
    )
    opacity_slider = mo.ui.slider(
        start=0.1, stop=1.0, step=0.1, value=0.8, show_value=True, label="Opacity"
    )
    mo.hstack([radius_slider, opacity_slider], justify="start", gap=2)
    return opacity_slider, radius_slider


@app.cell
def _(df, dgl, mo, opacity_slider, radius_slider):
    widget = mo.ui.anywidget(
        dgl.ScatterplotLayer(
            data=df.to_dict("records"),
            get_position=["lon", "lat"],
            get_fill_color=[255, 140, 0],
            get_radius=1,
            radius_scale=radius_slider.value,
            radius_min_pixels=2,
            radius_max_pixels=20,
            opacity=opacity_slider.value,
            center=(-98, 39),
            zoom=4,
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
    | Pitch | {_fmt(viewport.get('pitch'), '.1f')} |
    | Bearing | {_fmt(viewport.get('bearing'), '.1f')} |
    """
    )
    return


if __name__ == "__main__":
    app.run()
