# Basemaps

The basemap is a MapLibre GL style — deck.gl renders as an overlay on top
of it. Pick a bundled alias or point at any MapLibre-compatible style URL:

```python
dgl.Basemaps.list_available()
# ['bright', 'dark', 'dark-matter', 'liberty', 'light', 'none', 'osm',
#  'positron', 'voyager']

dgl.Map(basemap="dark-matter")                                 # alias
dgl.Map(basemap="https://tiles.example.com/style.json")        # any style URL
dgl.Map(basemap="none")                                        # no basemap
```

## Bundled aliases

| Alias | Source | Look |
|---|---|---|
| `dark-matter`, `dark` | CARTO | Dark gray, label-light — best for bright data colors |
| `positron`, `light` | CARTO | Light gray, minimal |
| `voyager` | CARTO | Colorful general-purpose |
| `liberty`, `osm` | OpenFreeMap | Full OSM cartography |
| `bright` | OpenFreeMap | High-contrast OSM |
| `positron` (OFM) | OpenFreeMap | Light minimal |
| `none` | — | Solid background, layers only |

CARTO and OpenFreeMap styles are free to use without an API key.

## Choosing a basemap

- **Data-dense overlays** → `dark-matter` or `positron`: neutral
  backgrounds keep attention on your layers.
- **Context/navigation matters** → `liberty` or `voyager`: richer
  cartography, streets and POI labels.
- **Benchmarks / pure data** → `none`: no tile traffic at all.

## Switching at runtime

```python
deck_map.basemap_style = dgl.Basemaps.resolve("voyager")
```

## Custom tile servers and WMS

Any URL returning a [MapLibre style document](https://maplibre.org/maplibre-style-spec/)
works. But you don't need to hand-write style JSON: the
`deckgl_marimo.maplibre` module composes a base style with extra sources
and MapLibre layers from Python — the primary reason this library uses
MapLibre for base layers:

```python
from deckgl_marimo.maplibre import MapLibreConfig, RasterSource, RasterLayer

config = MapLibreConfig(
    style="positron",                       # alias, URL, or inline spec
    sources={
        "topo": RasterSource.from_wms(
            base_url="https://ows.terrestris.de/osm/service",
            layers="TOPO-WMS",
        ),
    },
    map_layers=[RasterLayer(id="topo", source="topo", raster_opacity=0.7)],
)
m = dgl.Map(basemap=config, layers=[...])
```

`RasterSource.from_wms` builds the GetMap tile-URL template (WMS 1.1.1 or
1.3.x) for you. Also available: plain XYZ `RasterSource`, `VectorSource`
(PBF/MVT + `promote_id`), `GeoJSONSource` (with clustering), and typed
style layers (`FillLayer`, `LineLayer`, `RasterLayer`, `CircleLayer`,
`SymbolLayer`, `FillExtrusionLayer`). Use
`deckgl_marimo.maplibre.empty_style()` for WMS-only maps with no base
style. Swap the whole composition at runtime by assigning
`m.maplibre_config = config.to_dict()`.

See `examples/16_maplibre_wms.py` for a runnable demo and the
[MapLibre API reference](../api/maplibre.md).
