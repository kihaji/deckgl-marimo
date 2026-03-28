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
    mo.md("""
# Comprehensive Map Example

This notebook demonstrates **multi-layer composition** with the `Map` widget,
including a basemap picker, layer visibility toggles, reactive controls,
and click/hover readback.
""")
    return


@app.cell
def _(pd):
    cities = pd.DataFrame(
        [
            {"city": "New York", "lon": -74.006, "lat": 40.7128, "pop": 8336},
            {"city": "Los Angeles", "lon": -118.2437, "lat": 34.0522, "pop": 3979},
            {"city": "Chicago", "lon": -87.6298, "lat": 41.8781, "pop": 2693},
            {"city": "Houston", "lon": -95.3698, "lat": 29.7604, "pop": 2320},
            {"city": "Phoenix", "lon": -112.074, "lat": 33.4484, "pop": 1681},
            {"city": "Philadelphia", "lon": -75.1652, "lat": 39.9526, "pop": 1603},
            {"city": "San Antonio", "lon": -98.4936, "lat": 29.4241, "pop": 1547},
            {"city": "San Diego", "lon": -117.1611, "lat": 32.7157, "pop": 1424},
            {"city": "Dallas", "lon": -96.797, "lat": 32.7767, "pop": 1343},
            {"city": "San Jose", "lon": -121.8863, "lat": 37.3382, "pop": 1021},
        ]
    )
    return (cities,)


@app.cell
def _(pd):
    flights = pd.DataFrame(
        [
            {"src_lon": -74.006, "src_lat": 40.7128, "dst_lon": -118.2437, "dst_lat": 34.0522},
            {"src_lon": -74.006, "src_lat": 40.7128, "dst_lon": -87.6298, "dst_lat": 41.8781},
            {"src_lon": -74.006, "src_lat": 40.7128, "dst_lon": -95.3698, "dst_lat": 29.7604},
            {"src_lon": -118.2437, "src_lat": 34.0522, "dst_lon": -87.6298, "dst_lat": 41.8781},
            {"src_lon": -118.2437, "src_lat": 34.0522, "dst_lon": -121.8863, "dst_lat": 37.3382},
            {"src_lon": -87.6298, "src_lat": 41.8781, "dst_lon": -95.3698, "dst_lat": 29.7604},
            {"src_lon": -87.6298, "src_lat": 41.8781, "dst_lon": -75.1652, "dst_lat": 39.9526},
            {"src_lon": -112.074, "src_lat": 33.4484, "dst_lon": -117.1611, "dst_lat": 32.7157},
            {"src_lon": -96.797, "src_lat": 32.7767, "dst_lon": -98.4936, "dst_lat": 29.4241},
        ]
    )
    return (flights,)


@app.cell
def _(dgl, mo):
    basemap_options = {name: name for name in dgl.Basemaps.list_available() if name != "none" and name != "embedded"}
    basemap_picker = mo.ui.dropdown(
        options=basemap_options,
        value="dark-matter",
        label="Basemap",
    )
    return (basemap_picker,)


@app.cell
def _(mo):
    show_columns = mo.ui.switch(value=True, label="Columns")
    show_arcs = mo.ui.switch(value=True, label="Arcs")
    show_labels = mo.ui.switch(value=True, label="Labels")
    return show_arcs, show_columns, show_labels


@app.cell
def _(mo):
    radius_slider = mo.ui.slider(
        start=5000, stop=50000, step=5000, value=20000, show_value=True, label="Column Radius"
    )
    elevation_slider = mo.ui.slider(
        start=10, stop=500, step=10, value=100, show_value=True, label="Elevation Scale"
    )
    arc_width_slider = mo.ui.slider(
        start=1, stop=10, step=1, value=2, show_value=True, label="Arc Width"
    )
    return arc_width_slider, elevation_slider, radius_slider


@app.cell
def _(
    arc_width_slider,
    basemap_picker,
    elevation_slider,
    mo,
    radius_slider,
    show_arcs,
    show_columns,
    show_labels,
):
    mo.hstack(
        [
            mo.vstack([basemap_picker, mo.hstack([show_columns, show_arcs, show_labels], gap=1)]),
            mo.vstack([radius_slider, elevation_slider, arc_width_slider]),
        ],
        justify="start",
        gap=4,
    )
    return


@app.cell
def _(
    arc_width_slider,
    basemap_picker,
    cities,
    dgl,
    elevation_slider,
    flights,
    mo,
    radius_slider,
    show_arcs,
    show_columns,
    show_labels,
):
    layers = []

    if show_columns.value:
        layers.append(
            dgl.ColumnLayer(
                id="city-columns",
                data=cities.to_dict("records"),
                get_position=["lon", "lat"],
                get_fill_color=[0, 180, 230, 200],
                get_elevation="pop",
                elevation_scale=elevation_slider.value,
                radius=radius_slider.value,
                extruded=True,
                pickable=True,
            )
        )

    if show_arcs.value:
        layers.append(
            dgl.ArcLayer(
                id="flight-arcs",
                data=flights.to_dict("records"),
                get_source_position=["src_lon", "src_lat"],
                get_target_position=["dst_lon", "dst_lat"],
                get_source_color=[0, 128, 255],
                get_target_color=[255, 0, 128],
                get_width=arc_width_slider.value,
            )
        )

    if show_labels.value:
        layers.append(
            dgl.TextLayer(
                id="city-labels",
                data=cities.to_dict("records"),
                get_position=["lon", "lat"],
                get_text="city",
                get_size=14,
                get_color=[255, 255, 255, 220],
                get_text_anchor="middle",
                get_alignment_baseline="bottom",
                font_family="Arial, sans-serif",
                billboard=True,
            )
        )

    widget = mo.ui.anywidget(
        dgl.Map(
            layers=layers,
            basemap=basemap_picker.value,
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
## Viewport

| Property | Value |
|----------|-------|
| Longitude | {_fmt(viewport.get('longitude'), '.4f')} |
| Latitude | {_fmt(viewport.get('latitude'), '.4f')} |
| Zoom | {_fmt(viewport.get('zoom'), '.2f')} |
| Pitch | {_fmt(viewport.get('pitch'), '.1f')} |
| Bearing | {_fmt(viewport.get('bearing'), '.1f')} |
"""
    )
    return (viewport,)


@app.cell
def _(mo, widget):
    click = widget.value.get("click_info", {})
    hover = widget.value.get("hover_info", {})

    click_text = "No object clicked yet."
    if click:
        obj = click.get("object", {})
        click_text = f"**Layer:** `{click.get('layer_id', '?')}`\n\n**Object:** `{obj}`"

    hover_text = "Hover over an object."
    if hover:
        obj = hover.get("object", {})
        hover_text = f"**Layer:** `{hover.get('layer_id', '?')}`\n\n**Object:** `{obj}`"

    mo.hstack(
        [
            mo.vstack([mo.md("## Last Click"), mo.md(click_text)]),
            mo.vstack([mo.md("## Last Hover"), mo.md(hover_text)]),
        ],
        justify="start",
        gap=4,
    )
    return


if __name__ == "__main__":
    app.run()
