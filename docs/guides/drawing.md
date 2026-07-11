# Drawing & Editing

Draw and edit features directly on the map — polygons, lines, points,
circles, rectangles — with the results arriving in Python as GeoJSON.
Powered by `@deck.gl-community/editable-layers`.

## Enable a drawing mode

```python
m = dgl.Map(
    basemap="positron",
    drawing_config=dgl.DrawingConfig(
        mode="draw_polygon",
        style=dgl.DrawingStyle(fill_color=[255, 140, 0, 100], line_width=2),
    ),
)
widget = m.as_widget()
```

**Modes:** `draw_polygon`, `draw_line`, `draw_point`, `draw_circle`,
`draw_rectangle`, `draw_square`, `modify` (drag vertices), `translate`
(drag whole features), `delete` (click a feature to remove it), `view`
(off).

Switch modes reactively by assigning
`m.drawing_config = dgl.DrawingConfig("modify").to_dict()` from any cell
— the map stays stable.

## Read the drawn features

```python
features = widget.value.get("drawing_features", {})   # GeoJSON FeatureCollection
event = widget.value.get("drawing_event", {})         # {"type", "featureCount", "timestamp"}
```

The cell re-runs whenever a feature is added, moved, edited, or deleted.
Feed the collection straight back into a `GeoJsonLayer`, run a spatial
query with it, or persist it.

## Seed or clear features from Python

```python
m.drawing_features = my_feature_collection     # seed
m.drawing_features = dict(dgl.EMPTY_FEATURE_COLLECTION)  # clear
```

## Selection and deletion

In `modify`/`translate` modes, clicking a feature selects it. To delete
the selection programmatically:

```python
m.drawing_config = dgl.DrawingConfig("modify", delete_selected=True).to_dict()
```

The frontend deletes the selected feature(s), emits a `deleteFeature`
event, and resets the flag. `delete` mode is the interactive
alternative: every click deletes the clicked feature.

## Interaction notes

- Drag-drawn shapes (`draw_circle`, `draw_rectangle`, `draw_square`)
  temporarily disable map panning; other modes keep it.
- Double-click zoom is disabled while any drawing mode is active
  (double-click finishes polygons/lines).
- Measurement tooltips show while drawing lines/circles; disable with
  `DrawingStyle(show_measurements=False)`.

See `examples/18_drawing.py` for a runnable demo with a mode switcher.
