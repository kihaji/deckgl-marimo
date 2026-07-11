# Quick Start

## A standalone layer

Any layer displays itself — no explicit map setup needed:

```python
import deckgl_marimo as dgl

layer = dgl.ScatterplotLayer(
    data=df,                                # pandas / polars / list of dicts / ...
    get_position=["longitude", "latitude"], # column names
    get_fill_color=[255, 140, 0],           # constant RGBA
    get_radius="population",                # per-row column
    radius_scale=10,
)
widget = layer.as_widget()
widget
```

`as_widget()` wraps the layer in `marimo.ui.anywidget`, giving you
reactive `.value` access to viewport and pick state.

## A multi-layer map

```python
m = dgl.Map(
    layers=[
        dgl.ScatterplotLayer(
            data=cities_df,
            get_position=["lon", "lat"],
            get_fill_color=[255, 140, 0],
            radius_min_pixels=3,
        ),
        dgl.ArcLayer(
            data=flights_df,
            get_source_position=["src_lon", "src_lat"],
            get_target_position=["dst_lon", "dst_lat"],
        ),
    ],
    basemap="dark-matter",
    center=(-98.5, 39.8),
    zoom=4,
    pitch=45,
)
widget = m.as_widget()
widget
```

## Accessors

Every `get_*` parameter accepts:

- a **constant** — `[255, 0, 0]`, `5.0`
- a **column name** — `"population"`
- a **list of columns** for vectors — `["lon", "lat"]`
- a **callable** — `lambda row: [row["v"], 0, 0, 255]`
- a **[ColorScale](../guides/color-scales.md)** (color accessors only)

## Fitting the view to data

```python
m.fit_bounds(dgl.compute_bounds(df, position=["lon", "lat"]), padding=40)
```

## Next steps

- [Reactive Patterns](../guides/reactive-patterns.md) — **read this before
  wiring sliders to your map**; it is the single most important pattern in
  this library.
- [Binary Data Transport](../guides/binary-data.md) — for 100k+ row datasets.
