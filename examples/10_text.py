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
        {"name": "London", "lon": -0.1276, "lat": 51.5074, "pop": 9.0},
        {"name": "Paris", "lon": 2.3522, "lat": 48.8566, "pop": 11.0},
        {"name": "Berlin", "lon": 13.4050, "lat": 52.5200, "pop": 3.6},
        {"name": "Madrid", "lon": -3.7038, "lat": 40.4168, "pop": 6.7},
        {"name": "Rome", "lon": 12.4964, "lat": 41.9028, "pop": 4.3},
        {"name": "Amsterdam", "lon": 4.9041, "lat": 52.3676, "pop": 1.1},
        {"name": "Brussels", "lon": 4.3517, "lat": 50.8503, "pop": 2.1},
        {"name": "Vienna", "lon": 16.3738, "lat": 48.2082, "pop": 1.9},
        {"name": "Prague", "lon": 14.4378, "lat": 50.0755, "pop": 1.3},
        {"name": "Warsaw", "lon": 21.0122, "lat": 52.2297, "pop": 1.8},
        {"name": "Stockholm", "lon": 18.0686, "lat": 59.3293, "pop": 1.6},
        {"name": "Copenhagen", "lon": 12.5683, "lat": 55.6761, "pop": 1.4},
        {"name": "Lisbon", "lon": -9.1393, "lat": 38.7223, "pop": 2.9},
        {"name": "Athens", "lon": 23.7275, "lat": 37.9838, "pop": 3.2},
        {"name": "Dublin", "lon": -6.2603, "lat": 53.3498, "pop": 1.4},
    ]
    mo.md(f"**TextLayer** — **{len(cities)}** European capitals with population (millions)")
    return (cities,)


@app.cell
def _(mo):
    size_slider = mo.ui.slider(
        start=8, stop=48, step=4, value=20, show_value=True, label="Font Size"
    )
    mo.hstack([size_slider], justify="start", gap=2)
    return (size_slider,)


@app.cell
def _(dgl, mo):
    map_widget = dgl.Map(basemap="dark-matter", center=(10, 50), zoom=4)
    widget = map_widget.as_widget()
    return map_widget, widget


@app.cell
def _(widget):
    widget
    return


@app.cell
def _(cities, dgl, map_widget, size_slider):
    map_widget.layer_specs = [
        dgl.TextLayer(
            data=cities,
            get_position=["lon", "lat"],
            get_text="name",
            get_size=size_slider.value,
            get_color=[255, 255, 255, 230],
            get_text_anchor="middle",
            get_alignment_baseline="center",
            font_family="Arial, sans-serif",
            billboard=True,
            pickable=True,
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
