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
    import deckgl_marimo as dgl

    return (dgl,)


@app.cell
def _(mo):
    routes = [
        {
            "name": "Bay Bridge",
            "color": [255, 0, 0],
            "path": [
                [-122.3907, 37.7914],
                [-122.3716, 37.7892],
                [-122.3542, 37.7876],
                [-122.3322, 37.7858],
                [-122.3172, 37.7948],
            ],
        },
        {
            "name": "Golden Gate Bridge",
            "color": [255, 165, 0],
            "path": [
                [-122.4783, 37.8100],
                [-122.4745, 37.8120],
                [-122.4710, 37.8155],
                [-122.4690, 37.8200],
                [-122.4680, 37.8270],
            ],
        },
        {
            "name": "Market Street",
            "color": [0, 200, 255],
            "path": [
                [-122.3950, 37.7916],
                [-122.4050, 37.7880],
                [-122.4150, 37.7840],
                [-122.4250, 37.7800],
                [-122.4350, 37.7762],
            ],
        },
        {
            "name": "Embarcadero",
            "color": [0, 255, 100],
            "path": [
                [-122.3890, 37.7952],
                [-122.3930, 37.7980],
                [-122.3960, 37.8020],
                [-122.3980, 37.8060],
                [-122.3988, 37.8100],
                [-122.3985, 37.8140],
            ],
        },
    ]
    mo.md(f"**PathLayer** — **{len(routes)}** routes in San Francisco")
    return (routes,)


@app.cell
def _(mo):
    width_slider = mo.ui.slider(
        start=1, stop=20, step=1, value=5, show_value=True, label="Width"
    )
    rounded_toggle = mo.ui.switch(value=True, label="Rounded Joints")
    mo.hstack([width_slider, rounded_toggle], justify="start", gap=2)
    return rounded_toggle, width_slider


@app.cell
def _(dgl, mo, rounded_toggle, routes, width_slider):
    widget = mo.ui.anywidget(
        dgl.Map(
            layers=[
                dgl.PathLayer(
                    data=routes,
                    get_path="path",
                    get_color="color",
                    get_width=width_slider.value,
                    width_min_pixels=2,
                    rounded=rounded_toggle.value,
                ),
            ],
            basemap="dark-matter",
            center=(-122.42, 37.80),
            zoom=13,
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
