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
def _(mo):
    locations = [
        {"name": "Statue of Liberty", "lon": -74.0445, "lat": 40.6892, "icon": "marker"},
        {"name": "Empire State", "lon": -73.9857, "lat": 40.7484, "icon": "marker"},
        {"name": "Central Park", "lon": -73.9654, "lat": 40.7829, "icon": "marker"},
        {"name": "Brooklyn Bridge", "lon": -73.9969, "lat": 40.7061, "icon": "marker"},
        {"name": "Times Square", "lon": -73.9855, "lat": 40.758, "icon": "marker"},
        {"name": "One WTC", "lon": -74.0134, "lat": 40.7127, "icon": "marker"},
        {"name": "Grand Central", "lon": -73.9772, "lat": 40.7527, "icon": "marker"},
        {"name": "Met Museum", "lon": -73.9632, "lat": 40.7794, "icon": "marker"},
    ]
    mo.md(f"**IconLayer** — **{len(locations)}** NYC landmarks")
    return (locations,)


@app.cell
def _(mo):
    size_slider = mo.ui.slider(
        start=1, stop=20, step=1, value=8, show_value=True, label="Icon Size"
    )
    mo.hstack([size_slider], justify="start", gap=2)
    return (size_slider,)


@app.cell
def _(dgl, locations, mo, size_slider):
    ICON_ATLAS = "https://raw.githubusercontent.com/visgl/deck.gl-data/master/website/icon-atlas.png"
    ICON_MAPPING = {
        "marker": {"x": 0, "y": 0, "width": 128, "height": 128, "anchorY": 128, "mask": True},
    }
    widget = mo.ui.anywidget(
        dgl.Map(
            layers=[
                dgl.IconLayer(
                    data=locations,
                    get_position=["lon", "lat"],
                    get_icon="icon",
                    get_size=size_slider.value,
                    get_color=[255, 64, 64],
                    icon_atlas=ICON_ATLAS,
                    icon_mapping=ICON_MAPPING,
                    size_scale=1,
                    pickable=True,
                ),
            ],
            basemap="voyager",
            center=(-73.99, 40.74),
            zoom=12,
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
