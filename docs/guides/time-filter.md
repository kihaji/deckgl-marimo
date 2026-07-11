# Time Filter & Animation

Filter data by a time column **on the GPU** and animate a sliding window
at 60 fps — the data is uploaded once and never re-serialized during
playback (deck.gl `DataFilterExtension`).

## 1. Give the layer a filter accessor

```python
layer = dgl.ScatterplotLayer(
    data=points,
    get_position=["lon", "lat"],
    get_filter_value="t",          # numeric time column
)
```

`get_filter_value` auto-attaches the `DataFilterExtension`. Keep values
float32-safe — *seconds/days since your domain start*, not raw epoch
seconds (the GPU filter uses 32-bit floats).

## 2. Drive the animation

```python
domain = dgl.compute_time_domain(points, "t")          # [t_min, t_max]
deck_map = dgl.Map(layers=[layer], time_filter=dgl.build_time_filter(
    domain,
    window=(domain[1] - domain[0]) * 0.1,  # visible slice [T-window, T]
    playing=True,
    soft_edge=2.0,                          # optional fade in/out
))
```

Playback runs entirely client-side; the widget reports the throttled head
time back as `current_time`:

```python
mo.md(f"t = {widget.value.get('current_time', 0):.1f}")
```

Reassign `deck_map.time_filter = dgl.build_time_filter(...)` from a
reactive cell to play/pause, scrub (`current=`), or change the window.

## The pure-reactive alternative

In marimo you can skip the client-side animation entirely and drive the
GPU window from a slider — no playback loop, just traitlet sync:

```python
t = mo.ui.slider(0, 100, value=50, label="t")

# reactive cell
deck_map.set_layers([
    dgl.ScatterplotLayer(
        data=points,
        get_position=["lon", "lat"],
        get_filter_value="t",
        filter_range=[t.value - 10, t.value],
    )
])
```

Use `time_filter` for smooth autonomous playback; use `filter_range` when
a marimo control should own the clock.

See `examples/17_time_filter.py` for a runnable 100k-point demo.
