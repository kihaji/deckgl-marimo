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
    cities = pd.DataFrame(
        [
            {"city": "New York", "lon": -74.006, "lat": 40.7128, "population": 8336, "color": [255, 0, 0, 200]},
            {"city": "Los Angeles", "lon": -118.2437, "lat": 34.0522, "population": 3979, "color": [255, 165, 0, 200]},
            {"city": "Chicago", "lon": -87.6298, "lat": 41.8781, "population": 2693, "color": [0, 128, 255, 200]},
            {"city": "Houston", "lon": -95.3698, "lat": 29.7604, "population": 2320, "color": [0, 200, 100, 200]},
            {"city": "Phoenix", "lon": -112.074, "lat": 33.4484, "population": 1681, "color": [200, 0, 255, 200]},
            {"city": "Philadelphia", "lon": -75.1652, "lat": 39.9526, "population": 1603, "color": [255, 255, 0, 200]},
            {"city": "San Antonio", "lon": -98.4936, "lat": 29.4241, "population": 1547, "color": [0, 255, 200, 200]},
            {"city": "San Diego", "lon": -117.1611, "lat": 32.7157, "population": 1424, "color": [128, 0, 255, 200]},
            {"city": "Dallas", "lon": -96.797, "lat": 32.7767, "population": 1343, "color": [255, 100, 100, 200]},
            {"city": "San Jose", "lon": -121.8863, "lat": 37.3382, "population": 1021, "color": [100, 200, 255, 200]},
        ]
    )
    mo.md(f"**ColumnLayer** — **{len(cities)}** largest US cities by population (thousands)")
    return (cities,)


@app.cell
def _(mo):
    radius_slider = mo.ui.slider(
        start=5000, stop=50000, step=5000, value=20000, show_value=True, label="Radius (m)"
    )
    elevation_slider = mo.ui.slider(
        start=10, stop=500, step=10, value=100, show_value=True, label="Elevation Scale"
    )
    mo.hstack([radius_slider, elevation_slider], justify="start", gap=2)
    return elevation_slider, radius_slider


@app.cell
def _(cities, dgl, elevation_slider, mo, radius_slider):
    widget = mo.ui.anywidget(
        dgl.Map(
            layers=[
                dgl.ColumnLayer(
                    data=cities.to_dict("records"),
                    get_position=["lon", "lat"],
                    get_fill_color="color",
                    get_elevation="population",
                    elevation_scale=elevation_slider.value,
                    radius=radius_slider.value,
                    extruded=True,
                    pickable=True,
                ),
            ],
            basemap="dark-matter",
            center=(-98, 38),
            zoom=4,
            pitch=45,
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
"""
    )
    return (viewport,)


if __name__ == "__main__":
    app.run()
