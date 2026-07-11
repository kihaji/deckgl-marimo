# Binary Data Transport

For datasets with 100k+ rows, binary transport bypasses JSON serialization
entirely: data crosses the Python→JS boundary as packed typed arrays and
feeds deck.gl's native `data.attributes` format straight to the GPU.

**Measured at 200k polygons:**

| Mode | Serialization | Payload | |
|------|--------------|---------|---|
| JSON | 1,167 ms | 62 MB | |
| Binary | 39 ms | 14.5 MB | 30× faster, 4.3× smaller |

Supported on: `ScatterplotLayer`, `PolygonLayer`, `PathLayer`, `ArcLayer`,
`LineLayer`, `ColumnLayer`, `PointCloudLayer`.

## Simple: `use_binary=True`

```python
layer = dgl.ScatterplotLayer(
    data=large_df.to_dict("records"),
    get_position=["lon", "lat"],
    get_fill_color="color",     # per-row column
    get_radius="radius",
    use_binary=True,
)
```

Column accessors (and `ColorScale`/callable color accessors) are resolved
in Python and packed into the buffer; constant props stay in the spec.

!!! note
    The measured speedups above apply to the pre-built numpy path below.
    `use_binary=True` over a list of dicts still iterates rows in Python
    to build the arrays — much smaller payload, but packing time grows
    with row count.

## Fastest: pre-built numpy arrays

Zero per-row iteration — hand the packer ready-made arrays:

```python
import numpy as np
from deckgl_marimo import pack_binary

positions = np.column_stack([lons, lats]).astype(np.float32)
colors = np.asarray(color_data, dtype=np.uint8)     # (n, 4)

layer = dgl.ScatterplotLayer(radius_min_pixels=2, use_binary=True)
spec = layer.to_spec()

meta, buf = pack_binary(
    n=len(positions),
    attributes={
        "getPosition": (positions, "float32", 2),
        "getFillColor": (colors, "uint8", 4),
    },
)
meta["id"] = spec["id"]

deck_map.binary_metadata = {"layers": [meta]}
deck_map.binary_data = buf
deck_map.layer_specs = [spec]
```

For polygons there is `pack_polygon_binary` (handles vertex flattening and
`startIndices` for variable-length geometry).

## Layers can also take array dicts directly

Binary-capable layers accept a dict of pre-built arrays as `data`, which
routes through the fast path automatically:

```python
layer = dgl.ScatterplotLayer(
    data={"positions": positions, "colors": colors, "radii": radii},
    use_binary=True,
)
deck_map.set_layers([layer])
```

Fast-path keys per layer: `positions`/`colors`/`radii` (Scatterplot),
`source_positions`/`target_positions`/`source_colors`/`target_colors`
(Arc), `positions`/`colors`/`elevations` (Column),
`positions`/`colors`/`normals` (PointCloud), `path_coords`/`start_indices`/
`colors` (Path), `polygon_coords`/`start_indices`/`colors` (Polygon).

## Picking and tooltips still work

deck.gl picks binary layers by index; the widget back-fills the picked
row into `click_info`/`hover_info` on the Python side, and a `tooltip`
column is pre-packed for hover tooltips. See
[Picking & Events](picking-events.md).
