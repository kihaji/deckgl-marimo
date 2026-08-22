# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "deckgl-marimo",
# ]
#
# [tool.uv.sources]
# deckgl-marimo = { path = ".." }
# ///
"""Read an OGC WFS feature type as a deck.gl layer.

`WFSLayer` builds a GetFeature URL (GeoJSON output) and lets the browser
fetch it — no data passes through the kernel. The query parameters are
attributes, so `update_layer(..., bbox=m.bounds)` re-queries the visible
extent. Uses the public OpenLayers demo GeoServer.
"""

import marimo

__generated_with = "0.22.0"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo

    import deckgl_marimo as dgl
    from deckgl_marimo.wfs import WFSLayer

    return WFSLayer, dgl, mo


@app.cell
def _(mo):
    mo.md("""
    # WFS layer

    `topp:states` from https://ahocevar.com/geoserver/wfs, rendered as a
    `GeoJsonLayer`. Pan/zoom, then press the button to re-query only the
    visible extent (`bbox=m.bounds`).
    """)
    return


@app.cell
def _(WFSLayer, dgl):
    # Stable Map cell — the layer is updated in place below.
    WFS_URL = "https://ahocevar.com/geoserver/wfs"
    states = WFSLayer(
        url=WFS_URL,
        typename="topp:states",
        id="states",
        max_features=60,
        get_fill_color=(60, 120, 200, 90),
        get_line_color=(30, 60, 100, 255),
        line_width_min_pixels=1,
        pickable=True,
        auto_highlight=True,
    )
    deck_map = dgl.Map(layers=[states], basemap="positron", center=(-96, 38), zoom=3.5)
    widget = deck_map.as_widget()
    return deck_map, widget


@app.cell
def _(widget):
    widget
    return


@app.cell
def _(mo):
    refresh = mo.ui.run_button(label="Load features in view")
    refresh
    return (refresh,)


@app.cell
def _(deck_map, mo, refresh):
    # Re-query the visible extent. The button keeps this from firing on every pan.
    mo.stop(not refresh.value)
    bounds = deck_map.bounds
    if bounds is not None:
        deck_map.update_layer("states", bbox=bounds, max_features=60)
    mo.md(f"Requested bbox: `{bounds}`")
    return


@app.cell
def _(mo, widget):
    info = widget.value.get("click_info") or {}
    props = (info.get("object") or {}).get("properties") or {}
    mo.md(
        f"**Clicked:** {props.get('STATE_NAME', '—')} — population {props.get('PERSONS', '—')}"
        if props else "Click a state to see its attributes."
    )
    return


if __name__ == "__main__":
    app.run()
