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
    flights = pd.DataFrame(
        [
            {"src_lon": -122.4, "src_lat": 37.8, "dst_lon": -73.9, "dst_lat": 40.7, "route": "SFO → JFK"},
            {"src_lon": -122.4, "src_lat": 37.8, "dst_lon": -87.6, "dst_lat": 41.9, "route": "SFO → ORD"},
            {"src_lon": -122.4, "src_lat": 37.8, "dst_lon": -118.2, "dst_lat": 34.1, "route": "SFO → LAX"},
            {"src_lon": -73.9, "src_lat": 40.7, "dst_lon": -0.1, "dst_lat": 51.5, "route": "JFK → LHR"},
            {"src_lon": -73.9, "src_lat": 40.7, "dst_lon": 2.3, "dst_lat": 48.9, "route": "JFK → CDG"},
            {"src_lon": -73.9, "src_lat": 40.7, "dst_lon": -87.6, "dst_lat": 41.9, "route": "JFK → ORD"},
            {"src_lon": -118.2, "src_lat": 34.1, "dst_lon": 139.7, "dst_lat": 35.7, "route": "LAX → NRT"},
            {"src_lon": -118.2, "src_lat": 34.1, "dst_lon": -73.9, "dst_lat": 40.7, "route": "LAX → JFK"},
            {"src_lon": -87.6, "src_lat": 41.9, "dst_lon": -0.1, "dst_lat": 51.5, "route": "ORD → LHR"},
            {"src_lon": 2.3, "src_lat": 48.9, "dst_lon": 139.7, "dst_lat": 35.7, "route": "CDG → NRT"},
        ]
    )
    mo.md(f"**ArcLayer** — **{len(flights)}** flight routes between major cities")
    return (flights,)


@app.cell
def _(mo):
    width_slider = mo.ui.slider(
        start=1, stop=10, step=1, value=2, show_value=True, label="Arc Width"
    )
    great_circle_toggle = mo.ui.switch(value=True, label="Great Circle")
    mo.hstack([width_slider, great_circle_toggle], justify="start", gap=2)
    return great_circle_toggle, width_slider


@app.cell
def _(dgl, mo):
    map_widget = dgl.Map(basemap="dark-matter", center=(-40, 40), zoom=2)
    widget = mo.ui.anywidget(map_widget)
    return map_widget, widget


@app.cell
def _(widget):
    widget
    return


@app.cell
def _(dgl, flights, great_circle_toggle, map_widget, width_slider):
    map_widget.layer_specs = [
        dgl.ArcLayer(
            data=flights.to_dict("records"),
            get_source_position=["src_lon", "src_lat"],
            get_target_position=["dst_lon", "dst_lat"],
            get_source_color=[0, 128, 255],
            get_target_color=[255, 0, 128],
            get_width=width_slider.value,
            great_circle=great_circle_toggle.value,
        ).to_spec()
    ]
    return


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
    return


if __name__ == "__main__":
    app.run()
