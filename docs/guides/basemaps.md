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
works, including styles that reference your own raster/WMS tile sources —
this is the primary reason deckgl-marimo uses MapLibre for base layers.
Typed style composition from Python (adding WMS sources to a named style
without hand-writing style JSON) is tracked in
[issue #35](https://github.com/kihaji/deckgl-marimo/issues/35).
