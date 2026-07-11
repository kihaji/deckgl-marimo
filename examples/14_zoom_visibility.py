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
    cities = [
        {"name": "London", "lon": -0.1276, "lat": 51.5074},
        {"name": "Paris", "lon": 2.3522, "lat": 48.8566},
        {"name": "Berlin", "lon": 13.4050, "lat": 52.5200},
        {"name": "Madrid", "lon": -3.7038, "lat": 40.4168},
        {"name": "Rome", "lon": 12.4964, "lat": 41.9028},
        {"name": "Amsterdam", "lon": 4.9041, "lat": 52.3676},
        {"name": "Vienna", "lon": 16.3738, "lat": 48.2082},
        {"name": "Warsaw", "lon": 21.0122, "lat": 52.2297},
        {"name": "Stockholm", "lon": 18.0686, "lat": 59.3293},
        {"name": "Lisbon", "lon": -9.1393, "lat": 38.7223},
        {"name": "Athens", "lon": 23.7275, "lat": 37.9838},
        {"name": "Dublin", "lon": -6.2603, "lat": 53.3498},
    ]
    mo.md(
        "**Per-layer zoom visibility** — scatter dots are always visible; "
        "labels only appear when you zoom in past level 5."
    )
    return (cities,)


@app.cell
def _(mo):
    label_min_zoom = mo.ui.slider(
        start=3, stop=10, step=0.5, value=5, show_value=True,
        label="Label visible_min_zoom",
    )
    mo.hstack([label_min_zoom], justify="start", gap=2)
    return (label_min_zoom,)


@app.cell
def _(cities, dgl, label_min_zoom):
    dots = dgl.ScatterplotLayer(
        data=cities,
        get_position=["lon", "lat"],
        get_fill_color=[0, 180, 255, 220],
        get_radius=30000,
        radius_min_pixels=4,
        pickable=True,
    )
    labels = dgl.TextLayer(
        data=cities,
        get_position=["lon", "lat"],
        get_text="name",
        get_size=16,
        get_color=[255, 255, 255, 230],
        get_text_anchor="middle",
        get_alignment_baseline="bottom",
        get_pixel_offset=[0, -12],
        billboard=True,
        visible_min_zoom=label_min_zoom.value,
    )
    return dots, labels


@app.cell
def _(dgl, dots, labels, mo):
    map_widget = dgl.Map(
        basemap="dark-matter",
        center=(10, 50),
        zoom=4,
        layers=[dots, labels],
    )
    widget = map_widget.as_widget()
    return map_widget, widget


@app.cell
def _(widget):
    widget
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
