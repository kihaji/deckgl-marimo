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

__generated_with = "0.23.4"
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
    opacity_slider = mo.ui.slider(start=0.1, stop=1.0, step=0.1, value=0.7, show_value=True, label="Opacity")
    extruded_toggle = mo.ui.switch(value=True, label="3D Extrusion")
    line_width_slider = mo.ui.slider(start=0, stop=5, step=1, value=1, show_value=True, label="Line Width")
    mo.hstack([opacity_slider, extruded_toggle, line_width_slider], justify="start", gap=2)
    return extruded_toggle, line_width_slider, opacity_slider


@app.cell
def _(dgl):
    map_widget = dgl.Map(basemap="dark-matter", center=(-123.1, 49.25), zoom=11, pitch=45)
    widget = map_widget.as_widget()
    return map_widget, widget


@app.cell
def _(dgl, extruded_toggle, line_width_slider, map_widget, opacity_slider):
    GEOJSON_URL = "https://raw.githubusercontent.com/visgl/deck.gl-data/master/examples/geojson/vancouver-blocks.json"
    map_widget.layer_specs = [
        dgl.GeoJsonLayer(
            data=GEOJSON_URL,
            get_fill_color=[0, 180, 230, 160],
            get_line_color=[255, 255, 255],
            get_line_width=line_width_slider.value,
            extruded=extruded_toggle.value,
            opacity=opacity_slider.value,
            line_width_min_pixels=1,
        ).to_spec()
    ]
    return


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
