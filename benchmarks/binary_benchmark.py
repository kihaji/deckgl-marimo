# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "numpy",
#     "deckgl-marimo",
# ]
#
# [tool.uv.sources]
# deckgl-marimo = { path = ".." }
# ///
"""Parametrized JSON-vs-binary transport benchmark.

Replaces the seven near-identical ``*_binary_compare.py`` notebooks: pick a
layer type and row count, and compare serialization time and payload size
between the JSON path (``to_spec`` with materialized data) and the binary
path (``to_binary`` packed typed arrays), then view the binary result on a
live map.
"""

import marimo

__generated_with = "0.22.0"
app = marimo.App(width="full")


@app.cell
def _():
    import json
    import time

    import marimo as mo
    import numpy as np

    import deckgl_marimo as dgl

    return dgl, json, mo, np, time


@app.cell
def _(mo):
    layer_type = mo.ui.dropdown(
        options=[
            "ScatterplotLayer",
            "ArcLayer",
            "LineLayer",
            "ColumnLayer",
            "PointCloudLayer",
            "PathLayer",
            "PolygonLayer",
        ],
        value="ScatterplotLayer",
        label="Layer type",
    )
    n_rows = mo.ui.slider(
        start=10_000, stop=500_000, step=10_000, value=100_000,
        show_value=True, label="Rows",
    )
    mo.hstack([layer_type, n_rows], justify="start", gap=2)
    return layer_type, n_rows


@app.cell
def _(layer_type, n_rows, np):
    def _rng():
        return np.random.default_rng(42)

    def make_rows(kind: str, n: int) -> list[dict]:
        """Synthetic per-layer rows around Europe."""
        r = _rng()
        lon = r.uniform(-10, 20, n)
        lat = r.uniform(40, 55, n)
        color = np.column_stack([
            r.integers(0, 256, n), r.integers(0, 256, n),
            r.integers(0, 256, n), np.full(n, 200),
        ]).astype(int)

        if kind in ("ScatterplotLayer", "ColumnLayer", "PointCloudLayer"):
            rows = [
                {"lon": float(lon[i]), "lat": float(lat[i]),
                 "color": color[i].tolist(), "value": float(i % 1000)}
                for i in range(n)
            ]
            if kind == "PointCloudLayer":
                for row in rows:
                    row["pos"] = [row["lon"], row["lat"], (row["value"] % 100) * 50]
            return rows

        if kind in ("ArcLayer", "LineLayer"):
            dlon = r.uniform(-2, 2, n)
            dlat = r.uniform(-2, 2, n)
            return [
                {"src_lon": float(lon[i]), "src_lat": float(lat[i]),
                 "dst_lon": float(lon[i] + dlon[i]), "dst_lat": float(lat[i] + dlat[i]),
                 "color": color[i].tolist()}
                for i in range(n)
            ]

        if kind == "PathLayer":
            # 5-vertex random walks
            return [
                {"path": np.column_stack([
                    lon[i] + np.cumsum(r.uniform(-0.05, 0.05, 5)),
                    lat[i] + np.cumsum(r.uniform(-0.05, 0.05, 5)),
                ]).tolist(), "color": color[i].tolist()}
                for i in range(n)
            ]

        # PolygonLayer: small quads
        d = 0.02
        return [
            {"polygon": [
                [float(lon[i]), float(lat[i])],
                [float(lon[i] + d), float(lat[i])],
                [float(lon[i] + d), float(lat[i] + d)],
                [float(lon[i]), float(lat[i] + d)],
                [float(lon[i]), float(lat[i])],
            ], "color": color[i].tolist()}
            for i in range(n)
        ]

    rows = make_rows(layer_type.value, n_rows.value)
    return (rows,)


@app.cell
def _(dgl, layer_type, rows):
    def make_layer(kind: str, data, use_binary: bool):
        common = {"data": data, "use_binary": use_binary, "id": f"bench-{kind}"}
        if kind == "ScatterplotLayer":
            return dgl.ScatterplotLayer(
                get_position=["lon", "lat"], get_fill_color="color",
                radius_min_pixels=2, **common,
            )
        if kind == "ColumnLayer":
            return dgl.ColumnLayer(
                get_position=["lon", "lat"], get_fill_color="color",
                get_elevation="value", radius=500, **common,
            )
        if kind == "PointCloudLayer":
            return dgl.PointCloudLayer(
                get_position="pos", get_color="color", point_size=2, **common,
            )
        if kind == "ArcLayer":
            return dgl.ArcLayer(
                get_source_position=["src_lon", "src_lat"],
                get_target_position=["dst_lon", "dst_lat"], **common,
            )
        if kind == "LineLayer":
            return dgl.LineLayer(
                get_source_position=["src_lon", "src_lat"],
                get_target_position=["dst_lon", "dst_lat"],
                get_color="color", **common,
            )
        if kind == "PathLayer":
            return dgl.PathLayer(get_path="path", get_color="color", width_min_pixels=1, **common)
        return dgl.PolygonLayer(get_polygon="polygon", get_fill_color="color", **common)

    json_layer = make_layer(layer_type.value, rows, use_binary=False)
    binary_layer = make_layer(layer_type.value, rows, use_binary=True)
    return binary_layer, json_layer


@app.cell
def _(binary_layer, json, json_layer, mo, time):
    t0 = time.perf_counter()
    json_spec = json_layer.to_spec()
    json_payload = len(json.dumps(json_spec).encode())
    t_json = time.perf_counter() - t0

    t0 = time.perf_counter()
    _meta, _buf = binary_layer.to_binary()
    binary_spec = binary_layer.to_spec()
    binary_payload = len(_buf) + len(json.dumps({"layers": [_meta]}).encode()) + len(
        json.dumps(binary_spec).encode()
    )
    t_binary = time.perf_counter() - t0

    mo.md(f"""
## Results — {json_spec["type"]}

| Mode | Serialization | Payload |
|------|--------------|---------|
| JSON | {t_json * 1000:,.0f} ms | {json_payload / 1e6:,.1f} MB |
| Binary | {t_binary * 1000:,.0f} ms | {binary_payload / 1e6:,.1f} MB |
| **Ratio** | **{t_json / max(t_binary, 1e-9):,.1f}× faster** | **{json_payload / max(binary_payload, 1):,.1f}× smaller** |
""")
    return


@app.cell
def _(dgl):
    deck_map = dgl.Map(basemap="dark-matter", center=(5.0, 47.5), zoom=4)
    widget = deck_map.as_widget()
    return deck_map, widget


@app.cell
def _(widget):
    widget
    return


@app.cell
def _(binary_layer, deck_map):
    deck_map.set_layers([binary_layer])
    return


if __name__ == "__main__":
    app.run()
