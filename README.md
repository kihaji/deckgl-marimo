# deckgl-marimo

[![PyPI](https://img.shields.io/pypi/v/deckgl-marimo)](https://pypi.org/project/deckgl-marimo/)
[![Python](https://img.shields.io/pypi/pyversions/deckgl-marimo)](https://pypi.org/project/deckgl-marimo/)
[![CI](https://github.com/kihaji/deckgl-marimo/actions/workflows/ci.yml/badge.svg)](https://github.com/kihaji/deckgl-marimo/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Open in molab](https://marimo.io/molab-shield.svg)](https://molab.marimo.io/github/kihaji/deckgl-marimo/blob/main/examples/hexagon_example.py)

Interactive [deck.gl](https://deck.gl) visualization library for [marimo](https://marimo.io) notebooks. Render GPU-accelerated maps with 33 layer types, powered by [MapLibre GL](https://maplibre.org) and [anywidget](https://anywidget.dev).

## Features

- **10 deck.gl layer types** — scatter plots, hexagonal bins, heatmaps, arcs, paths, polygons, GeoJSON, 3D columns, and more
- **Multi-layer maps** — compose multiple layers on a single map
- **Standalone layers** — display any layer directly without explicit map setup
- **Marimo-native reactivity** — bind layer properties to sliders, dropdowns, and other widgets
- **Multiple data sources** — pandas, polars, geopandas, DuckDB, GeoJSON dicts, and URLs
- **Fully offline** — all JavaScript bundled in the package, no CDN dependencies
- **Viewport readback** — read the current map center, zoom, pitch, and bearing from Python
- **Click & hover events** — inspect picked objects reactively in downstream cells

## Installation

```bash
pip install deckgl-marimo
# or
uv add deckgl-marimo
```

## Quickstart

### Standalone layer

```python
import marimo as mo
import deckgl_marimo as dgl

layer = dgl.ScatterplotLayer(
    data=df,
    get_position=["longitude", "latitude"],
    get_fill_color=[255, 140, 0],
    get_radius="population",
    radius_scale=10,
)

# Displays a map with one layer
widget = mo.ui.anywidget(layer)
```

### Multi-layer map

```python
m = dgl.Map(
    layers=[
        dgl.ScatterplotLayer(
            data=cities_df,
            get_position=["lon", "lat"],
            get_fill_color=[255, 140, 0],
            get_radius=5,
            radius_min_pixels=3,
        ),
        dgl.ArcLayer(
            data=flights_df,
            get_source_position=["src_lon", "src_lat"],
            get_target_position=["dst_lon", "dst_lat"],
            get_source_color=[0, 128, 255],
            get_target_color=[255, 0, 128],
        ),
    ],
    basemap="dark-matter",
    center=(-98.5, 39.8),
    zoom=4,
    pitch=45,
)

widget = mo.ui.anywidget(m)
```

### Reactive controls

> **Important:** Create the `Map` widget in a cell that does **not** depend on
> slider values. Update layers by assigning to `map_widget.layer_specs` in a
> separate cell. This keeps the map instance stable — sliders update layers
> via traitlet sync instead of recreating the entire map, which would cause
> tile reloads and a black screen flash.

```python
# Cell 1 — sliders
radius = mo.ui.slider(200, 5000, value=1000, label="Radius")

# Cell 2 — create map widget (NO slider deps — stable, never re-executes)
map_widget = dgl.Map(basemap="dark-matter", center=(-1.4, 52.2), zoom=6, pitch=40)
widget = mo.ui.anywidget(map_widget)

# Cell 3 — display
widget

# Cell 4 — update layers reactively (re-executes when slider changes)
map_widget.layer_specs = [
    dgl.HexagonLayer(
        data=df,
        get_position=["lon", "lat"],
        radius=radius.value,
        extruded=True,
        elevation_scale=250,
    ).to_spec()
]

# Cell 5 — viewport readback
vp = widget.value.get("viewport", {})
mo.md(f"Zoom: {vp.get('zoom', 'N/A'):.1f}")
```

### DuckDB integration

```python
import duckdb

rel = duckdb.sql("SELECT lon, lat, value FROM 'data.parquet' WHERE value > 100")
layer = dgl.ScatterplotLayer(data=rel, get_position=["lon", "lat"])
```

## Available layers

### Fully tested (10)

| Layer | Use case |
|-------|----------|
| `ScatterplotLayer` | Point data |
| `GeoJsonLayer` | Polygons, lines, points from GeoJSON/GeoDataFrame |
| `ArcLayer` | Origin-destination flows |
| `PathLayer` | Routes, trajectories |
| `PolygonLayer` | Filled regions |
| `IconLayer` | Marker icons |
| `TextLayer` | Labels |
| `ColumnLayer` | 3D bars on map |
| `HexagonLayer` | Hexagonal binning |
| `HeatmapLayer` | Density visualization |

### Experimental (23)

All additional deck.gl layers are available as experimental stubs via `deckgl_marimo.layers`:

```python
from deckgl_marimo.layers import TripsLayer, MVTLayer, H3HexagonLayer, ContourLayer
# ... and 19 more
```

## Basemaps

```python
dgl.Basemaps.list_available()
# ['bright', 'dark', 'dark-matter', 'embedded', 'liberty', 'light', 'none', 'osm', 'positron', 'voyager']

# Use any MapLibre-compatible style URL
dgl.Map(basemap="https://my-tileserver.example.com/style.json")
```

## Troubleshooting

### `Content-Length` errors in the marimo console

You may see `h11._util.LocalProtocolError: Too little data for declared Content-Length`
in the server console when a notebook loads. This is a known issue with uvicorn's
default `h11` HTTP parser serving the large JS bundle. The map still works correctly.

To suppress it, install `httptools` so uvicorn uses a faster HTTP parser, then
**fully restart marimo** (kill and relaunch):

```bash
uv add httptools
# then restart marimo
uv run marimo edit your_notebook.py
```

## License

MIT
