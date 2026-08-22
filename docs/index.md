# deckgl-marimo

Interactive [deck.gl](https://deck.gl) visualization library for
[marimo](https://marimo.io) notebooks. Render GPU-accelerated maps with 15
fully tested layer types (plus experimental access to the full deck.gl
catalog), powered by [MapLibre GL](https://maplibre.org) and
[anywidget](https://anywidget.dev).

```python
import deckgl_marimo as dgl

layer = dgl.ScatterplotLayer(
    data=df,
    get_position=["longitude", "latitude"],
    get_fill_color=dgl.ColorScale("population", palette="viridis"),
    get_radius="population",
    radius_scale=10,
)
layer.as_widget()
```

## Why deckgl-marimo?

- **Scales with your data** — binary typed-array transport bypasses JSON
  serialization entirely (30× faster, 4× smaller payloads at 200k
  polygons). See [Binary Data Transport](guides/binary-data.md).
- **MapLibre basemaps** — stable WMS/tile-server support and clean,
  HTTP-retrievable style definitions under a performant deck.gl overlay.
- **marimo-native reactivity** — bind layer properties to sliders and
  read viewport (center, zoom, visible bounds) / click / hover state in
  downstream cells. See [Reactive Patterns](guides/reactive-patterns.md).
- **OGC WFS in and out** — render any WFS feature type, and edit it with
  the drawing tools, committing changes back as WFS-T transactions. See
  [WFS & WFS-T Editing](guides/wfs.md).
- **Bring your own DataFrame** — pandas, polars, geopandas, DuckDB,
  GeoJSON dicts, and URLs, via [narwhals](https://narwhals-dev.github.io/narwhals/)
  (no required backend).
- **Fully offline** — all JavaScript is bundled in the package; no CDN.

## At a glance

| | |
|---|---|
| Install | `pip install deckgl-marimo` |
| Quick start | [Getting Started](getting-started/quick-start.md) |
| The one pattern to know | [Reactive Patterns](guides/reactive-patterns.md) |
| Large datasets | [Binary Data Transport](guides/binary-data.md) |
| Source | [github.com/kihaji/deckgl-marimo](https://github.com/kihaji/deckgl-marimo) |
