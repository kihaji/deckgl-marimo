# Reactive Patterns in marimo

**This is the most important pattern in the library.** marimo re-runs a
cell whenever anything it depends on changes. If the cell that *creates*
your `Map` depends on a slider, every slider tick constructs a brand-new
widget: basemap tiles reload, the screen flashes black, and the camera
snaps back to its constructor defaults.

## The stable-map pattern

Create the map once, in a cell with **no** control dependencies; update
its layers from a separate cell:

```python
# Cell 1 — controls
radius = mo.ui.slider(200, 5000, value=1000, label="Radius")

# Cell 2 — create the map (NO slider deps — never re-executes)
deck_map = dgl.Map(basemap="dark-matter", center=(-1.4, 52.2), zoom=6, pitch=40)
widget = deck_map.as_widget()

# Cell 3 — display
widget

# Cell 4 — update layers reactively (re-executes on slider change)
deck_map.set_layers([
    dgl.HexagonLayer(
        data=df,
        get_position=["lon", "lat"],
        radius=radius.value,
        extruded=True,
    )
])

# Cell 5 — read state back
vp = widget.value.get("viewport", {})
mo.md(f"Zoom: {vp.get('zoom', 0):.1f}")

# Visible extent, lower-left / upper-right: ((west, south), (east, north))
bbox = deck_map.bounds   # None until the map has rendered once
```

Slider changes now flow to the existing widget through traitlet sync —
the map instance, its tiles, and your camera position all survive.

## Why `set_layers` and not `layer_specs`?

`Map.set_layers(layers)` re-serializes the layer specs **and** re-packs
binary buffers in one call. Assigning `map.layer_specs = [...]` directly
is the low-level escape hatch — it works for JSON layers but silently
skips binary re-packing, so binary layers (`use_binary=True`) break under
it.

## Other update methods

```python
deck_map.add_layer(layer)              # append one layer
deck_map.remove_layer("layer-id")      # remove by id
deck_map.update_layer("layer-id", get_radius=500, opacity=0.5)
```

`update_layer` validates prop names and suggests corrections for typos.

## The anti-pattern, for reference

```python
# DON'T: rebuilding the widget every slider change
dgl.Map(layers=[dgl.HexagonLayer(radius=radius.value, ...)]).as_widget()
```

This is an architectural consequence of marimo's fresh-instance-per-run
reactivity, not a bug ([issue #5](https://github.com/kihaji/deckgl-marimo/issues/5)
tracks ideas for preserving the camera across re-creation).
