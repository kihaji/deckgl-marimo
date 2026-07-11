# Examples

Runnable [marimo](https://marimo.io) notebooks, one concept each. Every
file is self-contained (inline script deps) so it also runs standalone in
[molab](https://molab.marimo.io):

```bash
uv run marimo edit examples/01_scatterplot.py
```

## Tutorials

| # | File | Demonstrates |
|---|------|--------------|
| 01 | [01_scatterplot.py](01_scatterplot.py) | ScatterplotLayer basics (airports) |
| 02 | [02_hexagon.py](02_hexagon.py) | HexagonLayer + the reactive stable-map pattern |
| 03 | [03_geojson.py](03_geojson.py) | GeoJsonLayer from GeoJSON/GeoDataFrame |
| 04 | [04_heatmap.py](04_heatmap.py) | HeatmapLayer density |
| 05 | [05_arc.py](05_arc.py) | ArcLayer origin→destination flows |
| 06 | [06_path.py](06_path.py) | PathLayer routes |
| 07 | [07_polygon.py](07_polygon.py) | PolygonLayer filled regions |
| 08 | [08_column.py](08_column.py) | ColumnLayer 3D bars |
| 09 | [09_icon.py](09_icon.py) | IconLayer markers |
| 10 | [10_text.py](10_text.py) | TextLayer labels |
| 11 | [11_comprehensive.py](11_comprehensive.py) | Multi-layer composition |
| 12 | [12_color_scale.py](12_color_scale.py) | ColorScale palettes and ramps |
| 13 | [13_polygon_color_scale.py](13_polygon_color_scale.py) | ColorScale on polygons |
| 14 | [14_zoom_visibility.py](14_zoom_visibility.py) | `visible_min_zoom`/`visible_max_zoom` gating |
| 15 | [15_polygon_zoom_visibility.py](15_polygon_zoom_visibility.py) | Zoom gating with polygon detail levels |
| 16 | [16_maplibre_wms.py](16_maplibre_wms.py) | Composed basemap: WMS source via `maplibre.MapLibreConfig` |
| 17 | [17_time_filter.py](17_time_filter.py) | GPU time filter: animated sliding window over 100k points |

## Feature demos

| File | Demonstrates |
|------|--------------|
| [hexagon_example.py](hexagon_example.py) | Slider-driven hexagon aggregation (the molab badge target in the main README) |
| [binary_picking.py](binary_picking.py) | Click/hover picking on binary-packed layers |
| [displacement.py](displacement.py) | DisplacementLayer (origin vs reported positions) |
| [ellipse.py](ellipse.py) | EllipseLayer (center/axes/orientation) |

## Elsewhere in the repo

- [`../benchmarks/`](../benchmarks/) — JSON-vs-binary transport benchmark
  (parametrized by layer type) and polygon stress tests.
- [`../repros/`](../repros/) — issue reproductions (not usage examples).

Notebooks here are deliberately self-contained rather than sharing a data
helper module — molab runs a single file in a sandbox, so imports from
sibling files would break the badge links.
