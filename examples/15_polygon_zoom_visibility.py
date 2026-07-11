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
    # Coarse region polygon: visible when zoomed out.
    region = [
        {
            "name": "San Francisco",
            "color": [0, 120, 200, 120],
            "polygon": [
                [-122.515, 37.708],
                [-122.355, 37.708],
                [-122.355, 37.832],
                [-122.515, 37.832],
                [-122.515, 37.708],
            ],
        },
    ]

    # Detailed neighborhood polygons: visible when zoomed in.
    neighborhoods = [
        {"name": "Financial District", "color": [0, 128, 255, 180], "polygon": [[-122.4000, 37.7900], [-122.3930, 37.7900], [-122.3930, 37.7960], [-122.4000, 37.7960]]},
        {"name": "Chinatown", "color": [255, 0, 128, 180], "polygon": [[-122.4100, 37.7930], [-122.4040, 37.7930], [-122.4040, 37.7980], [-122.4100, 37.7980]]},
        {"name": "North Beach", "color": [0, 200, 100, 180], "polygon": [[-122.4120, 37.7990], [-122.4040, 37.7990], [-122.4040, 37.8060], [-122.4120, 37.8060]]},
        {"name": "SOMA", "color": [255, 165, 0, 180], "polygon": [[-122.4100, 37.7780], [-122.3930, 37.7780], [-122.3930, 37.7880], [-122.4100, 37.7880]]},
        {"name": "Mission", "color": [200, 0, 255, 180], "polygon": [[-122.4230, 37.7580], [-122.4100, 37.7580], [-122.4100, 37.7700], [-122.4230, 37.7700]]},
    ]
    mo.md(
        "**PolygonLayer zoom visibility** — the blue SF outline shows when zoomed out; "
        "colored neighborhood polygons appear when you zoom in past the crossover."
    )
    return neighborhoods, region


@app.cell
def _(mo):
    crossover = mo.ui.slider(
        start=8, stop=14, step=0.5, value=11, show_value=True,
        label="Crossover zoom",
    )
    mo.hstack([crossover], justify="start", gap=2)
    return (crossover,)


@app.cell
def _(crossover, dgl, neighborhoods, region):
    region_layer = dgl.PolygonLayer(
        data=region,
        get_polygon="polygon",
        get_fill_color="color",
        get_line_color=[255, 255, 255, 220],
        get_line_width=3,
        line_width_min_pixels=2,
        stroked=True,
        filled=True,
        visible_max_zoom=crossover.value,
    )
    neighborhood_layer = dgl.PolygonLayer(
        data=neighborhoods,
        get_polygon="polygon",
        get_fill_color="color",
        get_line_color=[255, 255, 255],
        get_line_width=2,
        line_width_min_pixels=1,
        visible_min_zoom=crossover.value,
    )
    return neighborhood_layer, region_layer


@app.cell
def _(dgl, mo, neighborhood_layer, region_layer):
    map_widget = dgl.Map(
        basemap="dark-matter",
        center=(-122.43, 37.77),
        zoom=10,
        layers=[region_layer, neighborhood_layer],
    )
    widget = map_widget.as_widget()
    return map_widget, widget


@app.cell
def _(widget):
    widget
    return


@app.cell
def _(crossover, mo, widget):
    viewport = widget.value.get("viewport", {})
    zoom = viewport.get("zoom")

    def _fmt(val, spec):
        return format(val, spec) if isinstance(val, (int, float)) else "—"

    if isinstance(zoom, (int, float)):
        showing = "neighborhoods" if zoom >= crossover.value else "region outline"
    else:
        showing = "—"

    mo.md(
        f"""
**Viewport**

| Property | Value |
|----------|-------|
| Longitude | {_fmt(viewport.get('longitude'), '.4f')} |
| Latitude | {_fmt(viewport.get('latitude'), '.4f')} |
| Zoom | {_fmt(zoom, '.2f')} |
| Currently showing | {showing} |
"""
    )
    return


if __name__ == "__main__":
    app.run()
