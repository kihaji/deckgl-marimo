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

The current camera is always available:

```python
vp = widget.value.get("viewport", {})
# {"longitude": ..., "latitude": ..., "zoom": ..., "pitch": ..., "bearing": ...}
```
