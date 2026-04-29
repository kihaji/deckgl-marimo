# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
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
    import deckgl_marimo as dgl

    return (dgl,)


@app.cell
def _(mo):
    neighborhoods = [
        {"name": "Financial District", "elevation": 5000, "color": [0, 128, 255, 180], "polygon": [[-122.4000, 37.7900], [-122.3930, 37.7900], [-122.3930, 37.7960], [-122.4000, 37.7960]]},
        {"name": "Chinatown", "elevation": 3000, "color": [255, 0, 128, 180], "polygon": [[-122.4100, 37.7930], [-122.4040, 37.7930], [-122.4040, 37.7980], [-122.4100, 37.7980]]},
        {"name": "North Beach", "elevation": 4000, "color": [0, 200, 100, 180], "polygon": [[-122.4120, 37.7990], [-122.4040, 37.7990], [-122.4040, 37.8060], [-122.4120, 37.8060]]},
        {"name": "SOMA", "elevation": 6000, "color": [255, 165, 0, 180], "polygon": [[-122.4100, 37.7780], [-122.3930, 37.7780], [-122.3930, 37.7880], [-122.4100, 37.7880]]},
        {"name": "Mission", "elevation": 3500, "color": [200, 0, 255, 180], "polygon": [[-122.4230, 37.7580], [-122.4100, 37.7580], [-122.4100, 37.7700], [-122.4230, 37.7700]]},
    ]
    mo.md(f"**PolygonLayer** — **{len(neighborhoods)}** SF neighborhoods (synthetic data)")
    return (neighborhoods,)


@app.cell
def _(mo):
    extruded_toggle = mo.ui.switch(value=True, label="3D Extrusion")
    elevation_slider = mo.ui.slider(
        start=0.1, stop=5.0, step=0.1, value=1.0, show_value=True, label="Elevation Scale"
    )
    opacity_slider = mo.ui.slider(
        start=0.1, stop=1.0, step=0.1, value=0.8, show_value=True, label="Opacity"
    )
    mo.hstack([extruded_toggle, elevation_slider, opacity_slider], justify="start", gap=2)
    return elevation_slider, extruded_toggle, opacity_slider


@app.cell
def _(dgl, mo):
    map_widget = dgl.Map(basemap="dark-matter", center=(-122.41, 37.79), zoom=13, pitch=45)
    widget = map_widget.as_widget()
    return map_widget, widget


@app.cell
def _(widget):
    widget
    return


@app.cell
def _(dgl, elevation_slider, extruded_toggle, map_widget, neighborhoods, opacity_slider):
    map_widget.layer_specs = [
        dgl.PolygonLayer(
            data=neighborhoods,
            get_polygon="polygon",
            get_fill_color="color",
            get_line_color=[255, 255, 255],
            get_line_width=2,
            get_elevation="elevation",
            elevation_scale=elevation_slider.value,
            extruded=extruded_toggle.value,
            opacity=opacity_slider.value,
            line_width_min_pixels=1,
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
| Pitch | {_fmt(viewport.get('pitch'), '.1f')} |
"""
    )
    return


if __name__ == "__main__":
    app.run()
