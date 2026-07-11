# Color Scales

Map a numeric column through an interpolated color ramp with
[`ColorScale`](../api/color-scale.md) — usable with any `get_*_color`
accessor:

```python
# Named palette
dgl.ScatterplotLayer(
    data=df,
    get_position=["lon", "lat"],
    get_fill_color=dgl.ColorScale("temperature", palette="viridis"),
)

# Two-color ramp with log scaling
dgl.ScatterplotLayer(
    data=df,
    get_position=["lon", "lat"],
    get_fill_color=dgl.ColorScale("population", colors=["blue", "red"], scale="log"),
)
```

**Palettes:** `viridis`, `plasma`, `inferno`, `magma`, `cividis`,
`coolwarm`, `RdBu`, `spectral`, `turbo`.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `column` | *(required)* | Numeric column name to map |
| `palette` | — | Named palette (mutually exclusive with `colors`) |
| `colors` | — | 2+ colors: names (`"blue"`), hex (`"#FF0000"`), or RGB (`[255, 0, 0]`) |
| `domain` | auto | `(min, max)` value range; auto-detected from data if omitted |
| `scale` | `"linear"` | `"linear"` or `"log"` |
| `alpha` | `255` | Alpha channel (0–255) for all output colors |

## Callable accessors

For arbitrary per-row logic, pass a function instead:

```python
dgl.ScatterplotLayer(
    data=df,
    get_position=["lon", "lat"],
    get_fill_color=lambda row: [
        int(row["temperature"] * 2.55),
        50,
        255 - int(row["temperature"] * 2.55),
        200,
    ],
)
```

Both `ColorScale` and callables work with
[binary transport](binary-data.md) — colors resolve in Python and pack
into the buffer automatically.

!!! warning "Concrete data required"
    `ColorScale` and callable accessors materialize your data to compute
    per-row values, so they don't work with URL data. Load the data
    yourself first, or pre-compute a color column.
