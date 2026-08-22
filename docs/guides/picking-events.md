# Picking & Events

Layers are `pickable=True` by default. Clicks and hovers flow back to
Python through the `click_info` and `hover_info` traitlets:

```python
deck_map = dgl.Map(layers=[layer])
widget = deck_map.as_widget()

# In a downstream cell — re-runs whenever the user clicks the map
info = widget.value.get("click_info", {})
picked_row = info.get("object")        # the full data row
coordinate = info.get("coordinate")    # [lon, lat] under the cursor
layer_id = info.get("layer_id")
index = info.get("index")              # row index within the layer
```

`hover_info` has the same shape and updates as the pointer moves over
features.

## How binary layers stay pickable

With [binary transport](binary-data.md), deck.gl has no row objects to
hand back — a pick only carries the feature *index*. The widget bridges
this transparently: when a pick event arrives with `object: null`, the
Python side looks up the source row by index (cached per layer) and
back-fills `object`, so downstream code treats JSON and binary layers
identically.

## Tooltips

The default hover tooltip reads a `tooltip` key off the picked row:

```python
df["tooltip"] = df["name"] + ": " + df["value"].astype(str)
layer = dgl.ScatterplotLayer(data=df, get_position=["lon", "lat"])
```

For binary layers the tooltip strings are pre-packed at serialization
time and looked up by index in JS — same column, same behavior.

## Highlighting

```python
dgl.ScatterplotLayer(..., auto_highlight=True)
```

## Viewport readback

The current camera is always available — populated as soon as the map has
loaded and refreshed after every pan/zoom/rotate:

```python
vp = widget.value.get("viewport", {})
# {"longitude": ..., "latitude": ..., "zoom": ..., "pitch": ..., "bearing": ...,
#  "bounds": [[west, south], [east, north]]}
```

### Visible bounding box

`bounds` is the visible extent as **lower-left, upper-right** corners —
`[[west, south], [east, north]]`. The `Map` exposes it directly as a
property, already converted to tuples:

```python
deck_map.bounds
# ((-110.2, 30.1), (-80.9, 44.6))   or None before the first frontend report
```

It is the same shape `fit_bounds()` accepts, so you can snapshot and
restore a view, or feed the extent to a query:

```python
# Restore a saved extent
deck_map.fit_bounds(saved_bounds)

# Only load what is on screen (DuckDB example)
(west, south), (east, north) = deck_map.bounds
rel = duckdb.sql(f"""
    SELECT lon, lat, value FROM 'points.parquet'
    WHERE lon BETWEEN {west} AND {east} AND lat BETWEEN {south} AND {north}
""")
```

!!! note "Pitch and the antimeridian"
    With `pitch > 0` the visible area is a trapezoid; `bounds` is its
    axis-aligned bounding box, which grows quickly at high pitch near the
    horizon. Across the antimeridian MapLibre reports *unwrapped* longitudes
    (east may exceed 180°); they are passed through unchanged so
    `fit_bounds()` round-trips — normalize yourself if you need ±180.
