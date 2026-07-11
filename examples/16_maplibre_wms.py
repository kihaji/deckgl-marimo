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
"""Composed basemap: WMS raster source + deck.gl overlay.

Demonstrates the maplibre module — the reason this library uses MapLibre
for base layers: add a WMS topo layer onto a named basemap style from
Python, no hand-written style JSON, with a deck.gl scatterplot on top.
"""

import marimo

__generated_with = "0.22.0"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo

    import deckgl_marimo as dgl
    from deckgl_marimo.maplibre import MapLibreConfig, RasterLayer, RasterSource

    return MapLibreConfig, RasterLayer, RasterSource, dgl, mo


@app.cell
def _(mo):
    opacity = mo.ui.slider(0.0, 1.0, step=0.1, value=0.7, show_value=True, label="WMS opacity")
    opacity
    return (opacity,)


@app.cell
def _(MapLibreConfig, RasterLayer, RasterSource, dgl):
    # Stable Map cell (no slider deps). The config composes:
    #   positron base style  +  terrestris demo WMS  (+ deck.gl on top)
    deck_map = dgl.Map(
        basemap=MapLibreConfig(
            style="positron",
            sources={
                "topo-wms": RasterSource.from_wms(
                    base_url="https://ows.terrestris.de/osm/service",
                    layers="TOPO-WMS",
                    attribution="© terrestris",
                ),
            },
            map_layers=[
                RasterLayer(id="topo", source="topo-wms", raster_opacity=0.7),
            ],
        ),
        center=(7.1, 50.7),
        zoom=7,
    )
    widget = deck_map.as_widget()
    return deck_map, widget


@app.cell
def _(widget):
    widget
    return


@app.cell
def _(deck_map, dgl):
    # deck.gl overlay on top of the composed basemap
    cities = [
        {"name": "Köln", "lon": 6.96, "lat": 50.94, "pop": 1084},
        {"name": "Bonn", "lon": 7.10, "lat": 50.73, "pop": 331},
        {"name": "Koblenz", "lon": 7.59, "lat": 50.36, "pop": 114},
        {"name": "Frankfurt", "lon": 8.68, "lat": 50.11, "pop": 753},
    ]
    deck_map.set_layers([
        dgl.ScatterplotLayer(
            data=cities,
            get_position=["lon", "lat"],
            get_radius="pop",
            radius_scale=20,
            radius_min_pixels=4,
            get_fill_color=[220, 60, 60, 220],
        )
    ])
    return


@app.cell
def _(MapLibreConfig, RasterLayer, RasterSource, deck_map, opacity):
    # Reactive: swap the config when the slider moves (the map itself is stable)
    deck_map.maplibre_config = MapLibreConfig(
        style="positron",
        sources={
            "topo-wms": RasterSource.from_wms(
                base_url="https://ows.terrestris.de/osm/service",
                layers="TOPO-WMS",
                attribution="© terrestris",
            ),
        },
        map_layers=[
            RasterLayer(id="topo", source="topo-wms", raster_opacity=opacity.value),
        ],
    ).to_dict()
    return


if __name__ == "__main__":
    app.run()
