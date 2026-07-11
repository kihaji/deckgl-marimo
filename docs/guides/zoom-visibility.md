# Zoom-Gated Visibility

Show or hide layers based on the current zoom level — e.g. a heatmap when
zoomed out, individual points when zoomed in:

```python
overview = dgl.HeatmapLayer(
    data=df,
    get_position=["lon", "lat"],
    visible_max_zoom=8,          # visible at zoom <= 8
)
detail = dgl.ScatterplotLayer(
    data=df,
    get_position=["lon", "lat"],
    visible_min_zoom=8,          # visible at zoom >= 8
)
deck_map = dgl.Map(layers=[overview, detail])
```

Both bounds are inclusive and either can be omitted. The gating happens
entirely in the frontend as the user zooms — no Python round-trip, no
re-serialization.

A layer's own `visible=False` always wins: gating never resurrects a
layer you hid explicitly.

!!! note "`visible_min_zoom` vs deck.gl's `min_zoom`"
    Some deck.gl layers (e.g. the experimental `TileLayer`) have their own
    `min_zoom`/`max_zoom` props that control *data fetching*, not widget
    visibility. Those pass through to deck.gl untouched — the
    `visible_*` names are deliberately distinct so the two never collide.

See `examples/14_zoom_visibility.py` and
`examples/15_polygon_zoom_visibility.py` for runnable demos.
