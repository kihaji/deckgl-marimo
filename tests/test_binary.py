"""Tests for binary data packing."""

import pytest
import numpy as np

from deckgl_marimo._binary import pack_binary, pack_polygon_binary


class TestPackBinary:
    """Tests for the generic pack_binary function."""

    def test_fixed_size_no_start_indices(self):
        """Fixed-size layer (e.g., ScatterplotLayer) — no startIndices."""
        n = 100
        positions = np.random.rand(n, 2).astype(np.float32)
        colors = np.random.randint(0, 256, (n, 4), dtype=np.uint8)

        meta, buf = pack_binary(
            n,
            attributes={
                "getPosition": (positions, "float32", 2),
                "getFillColor": (colors, "uint8", 4),
            },
        )

        assert meta["length"] == n
        assert "startIndices" not in meta
        assert "getPosition" in meta["attributes"]
        assert "getFillColor" in meta["attributes"]

        pos_meta = meta["attributes"]["getPosition"]
        assert pos_meta["dtype"] == "float32"
        assert pos_meta["size"] == 2
        assert pos_meta["byteLength"] == n * 2 * 4  # n points * 2 floats * 4 bytes

        col_meta = meta["attributes"]["getFillColor"]
        assert col_meta["dtype"] == "uint8"
        assert col_meta["size"] == 4
        assert col_meta["byteLength"] == n * 4  # n points * 4 bytes

        assert len(buf) > 0

    def test_variable_length_with_start_indices(self):
        """Variable-length layer (e.g., PathLayer) — with startIndices."""
        n = 10
        verts_per = 5
        total_verts = n * verts_per
        coords = np.random.rand(total_verts, 2).astype(np.float32)
        si = np.arange(n, dtype=np.uint32) * verts_per

        meta, buf = pack_binary(
            n,
            attributes={"getPath": (coords, "float32", 2)},
            start_indices=si,
        )

        assert meta["length"] == n
        assert "startIndices" in meta
        assert meta["startIndices"]["dtype"] == "uint32"
        assert meta["startIndices"]["byteLength"] == n * 4
        assert meta["attributes"]["getPath"]["byteLength"] == total_verts * 2 * 4

    def test_single_attribute(self):
        """Minimal case: one attribute, no startIndices."""
        n = 50
        elevations = np.random.rand(n).astype(np.float32)

        meta, buf = pack_binary(
            n,
            attributes={"getElevation": (elevations, "float32", 1)},
        )

        assert meta["length"] == 50
        assert meta["attributes"]["getElevation"]["size"] == 1
        assert meta["attributes"]["getElevation"]["byteLength"] == 50 * 4

    def test_3d_positions(self):
        """3D positions (e.g., PointCloudLayer)."""
        n = 200
        positions = np.random.rand(n, 3).astype(np.float32)

        meta, buf = pack_binary(
            n,
            attributes={"getPosition": (positions, "float32", 3)},
        )

        assert meta["attributes"]["getPosition"]["size"] == 3
        assert meta["attributes"]["getPosition"]["byteLength"] == n * 3 * 4

    def test_alignment(self):
        """Offsets are properly aligned for their dtype."""
        n = 3
        # uint8 followed by float32 — float32 must be 4-byte aligned
        colors = np.array([1, 2, 3], dtype=np.uint8)
        positions = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]], dtype=np.float32)

        meta, buf = pack_binary(
            n,
            attributes={
                "getColor": (colors, "uint8", 1),
                "getPosition": (positions, "float32", 2),
            },
        )

        pos_offset = meta["attributes"]["getPosition"]["offset"]
        assert pos_offset % 4 == 0, f"float32 offset {pos_offset} not 4-byte aligned"

    def test_empty_data(self):
        """Zero-length data."""
        meta, buf = pack_binary(0, attributes={})
        assert meta["length"] == 0
        assert meta["attributes"] == {}
        assert buf == b""

    def test_buffer_roundtrip(self):
        """Values in buffer match input arrays."""
        n = 5
        positions = np.array([[i, i + 0.5] for i in range(n)], dtype=np.float32)

        meta, buf = pack_binary(
            n,
            attributes={"getPosition": (positions, "float32", 2)},
        )

        pos_meta = meta["attributes"]["getPosition"]
        recovered = np.frombuffer(
            buf, dtype=np.float32,
            count=pos_meta["byteLength"] // 4,
            offset=pos_meta["offset"],
        ).reshape(n, 2)

        np.testing.assert_array_equal(recovered, positions)


class TestPackPolygonBinary:
    """Tests for the polygon-specific packing function."""

    def test_fast_path_numpy_arrays(self):
        """Fast path with pre-built numpy arrays."""
        n = 10
        verts_per = 6
        total_verts = n * verts_per

        data = {
            "polygon_coords": np.random.rand(total_verts, 2).astype(np.float32),
            "start_indices": np.arange(n, dtype=np.uint32) * verts_per,
            "colors": np.random.randint(0, 256, (total_verts, 4), dtype=np.uint8),
        }

        meta, buf = pack_polygon_binary(data)

        assert meta["length"] == n
        assert "startIndices" in meta
        assert "getPolygon" in meta["attributes"]
        assert "getFillColor" in meta["attributes"]
        assert meta["attributes"]["getPolygon"]["dtype"] == "float32"
        assert meta["attributes"]["getPolygon"]["size"] == 2

    def test_fast_path_no_colors(self):
        """Fast path without color data."""
        n = 5
        verts_per = 4
        total_verts = n * verts_per

        data = {
            "polygon_coords": np.random.rand(total_verts, 2).astype(np.float32),
            "start_indices": np.arange(n, dtype=np.uint32) * verts_per,
            "colors": None,
        }

        meta, buf = pack_polygon_binary(data)

        assert "getPolygon" in meta["attributes"]
        assert "getFillColor" not in meta["attributes"]

    def test_slow_path_list_of_dicts(self):
        """Slow path with list of dicts."""
        data = [
            {"polygon": [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]], "color": [255, 0, 0, 200]},
            {"polygon": [[2, 2], [3, 2], [3, 3], [2, 2]], "color": [0, 255, 0, 200]},
        ]

        meta, buf = pack_polygon_binary(data, get_polygon="polygon", get_fill_color="color")

        assert meta["length"] == 2
        assert "startIndices" in meta
        assert "getPolygon" in meta["attributes"]
        assert "getFillColor" in meta["attributes"]

        # First polygon has 5 verts, second has 3
        si_meta = meta["startIndices"]
        si = np.frombuffer(buf, dtype=np.uint32, count=2, offset=si_meta["offset"])
        assert si[0] == 0
        assert si[1] == 5

    def test_slow_path_no_color_accessor(self):
        """Slow path without color accessor (constant color)."""
        data = [
            {"polygon": [[0, 0], [1, 0], [1, 1], [0, 0]]},
        ]

        meta, buf = pack_polygon_binary(data, get_polygon="polygon")

        assert "getPolygon" in meta["attributes"]
        assert "getFillColor" not in meta["attributes"]

    def test_coordinate_values_preserved(self):
        """Coordinates survive the packing round-trip."""
        data = [
            {"polygon": [[10.5, 20.5], [30.5, 40.5], [10.5, 20.5]]},
        ]

        meta, buf = pack_polygon_binary(data, get_polygon="polygon")

        pg_meta = meta["attributes"]["getPolygon"]
        coords = np.frombuffer(
            buf, dtype=np.float32,
            count=pg_meta["byteLength"] // 4,
            offset=pg_meta["offset"],
        ).reshape(-1, 2)

        np.testing.assert_allclose(coords[0], [10.5, 20.5], rtol=1e-6)
        np.testing.assert_allclose(coords[1], [30.5, 40.5], rtol=1e-6)


class TestLayerToBinary:
    """Tests for layer-level to_binary() methods."""

    def test_scatterplot_layer_binary(self):
        from deckgl_marimo.layers._core import ScatterplotLayer

        data = [
            {"lon": -122.4, "lat": 37.8, "color": [255, 0, 0, 200], "radius": 100.0},
            {"lon": -73.9, "lat": 40.7, "color": [0, 255, 0, 200], "radius": 200.0},
        ]
        layer = ScatterplotLayer(
            data=data, get_position=["lon", "lat"],
            get_fill_color="color", get_radius="radius",
            use_binary=True,
        )

        result = layer.to_binary()
        assert result is not None
        meta, buf = result
        assert meta["length"] == 2
        assert "getPosition" in meta["attributes"]
        assert "getFillColor" in meta["attributes"]
        assert "getRadius" in meta["attributes"]

    def test_scatterplot_layer_no_binary_by_default(self):
        from deckgl_marimo.layers._core import ScatterplotLayer

        layer = ScatterplotLayer(data=[{"lon": 0, "lat": 0}], get_position=["lon", "lat"])
        assert layer.to_binary() is None

    def test_polygon_layer_binary_uses_solid_type(self):
        from deckgl_marimo.layers._core import PolygonLayer

        data = [{"polygon": [[0, 0], [1, 0], [1, 1], [0, 0]], "color": [255, 0, 0, 200]}]
        layer = PolygonLayer(data=data, get_polygon="polygon", get_fill_color="color", use_binary=True)

        spec = layer.to_spec()
        assert spec["type"] == "SolidPolygonLayer"
        assert "getPolygon" not in spec

    def test_path_layer_binary(self):
        from deckgl_marimo.layers._core import PathLayer

        data = [
            {"path": [[0, 0], [1, 1], [2, 0]], "color": [255, 0, 0, 200]},
        ]
        layer = PathLayer(data=data, get_path="path", get_color="color", use_binary=True)

        result = layer.to_binary()
        assert result is not None
        meta, buf = result
        assert "startIndices" in meta
        assert "getPath" in meta["attributes"]
        assert "getColor" in meta["attributes"]

    def test_arc_layer_binary(self):
        from deckgl_marimo.layers._core import ArcLayer

        data = [
            {"src_lon": 0, "src_lat": 0, "tgt_lon": 1, "tgt_lat": 1,
             "src_color": [255, 0, 0, 200], "tgt_color": [0, 255, 0, 200]},
        ]
        layer = ArcLayer(
            data=data,
            get_source_position=["src_lon", "src_lat"],
            get_target_position=["tgt_lon", "tgt_lat"],
            get_source_color="src_color",
            get_target_color="tgt_color",
            use_binary=True,
        )

        result = layer.to_binary()
        assert result is not None
        meta, buf = result
        assert "getSourcePosition" in meta["attributes"]
        assert "getTargetPosition" in meta["attributes"]
        assert "getSourceColor" in meta["attributes"]
        assert "getTargetColor" in meta["attributes"]

    def test_column_layer_binary(self):
        from deckgl_marimo.layers._core import ColumnLayer

        data = [{"lon": 0, "lat": 0, "color": [255, 0, 0, 200], "elevation": 1000.0}]
        layer = ColumnLayer(
            data=data, get_position=["lon", "lat"],
            get_fill_color="color", get_elevation="elevation",
            use_binary=True,
        )

        result = layer.to_binary()
        assert result is not None
        meta, buf = result
        assert "getPosition" in meta["attributes"]
        assert "getFillColor" in meta["attributes"]
        assert "getElevation" in meta["attributes"]


class TestPolygonBinaryResolvedColors:
    """PolygonLayer.to_binary with ColorScale/callable fill colors (#19)."""

    def _unpack_colors(self, meta, buf, n_verts):
        np = pytest.importorskip("numpy")
        cm = meta["attributes"]["getFillColor"]
        raw = buf[cm["offset"] : cm["offset"] + cm["byteLength"]]
        return np.frombuffer(raw, dtype=np.uint8).reshape(n_verts, 4)

    def test_colorscale_expands_per_vertex_in_one_pass(self):
        from deckgl_marimo import ColorScale
        from deckgl_marimo.layers._core import PolygonLayer

        data = [
            {"polygon": [[0, 0], [1, 0], [1, 1], [0, 0]], "v": 0.0},
            {"polygon": [[2, 2], [3, 2], [3, 3], [2, 3], [2, 2]], "v": 100.0},
        ]
        layer = PolygonLayer(
            data=data,
            get_polygon="polygon",
            get_fill_color=ColorScale("v", palette="viridis"),
            use_binary=True,
        )
        meta, buf = layer.to_binary()

        assert meta["length"] == 2
        colors = self._unpack_colors(meta, buf, 9)  # 4 + 5 vertices
        # Every vertex of a polygon shares that polygon's resolved color
        assert len({tuple(c) for c in colors[:4]}) == 1
        assert len({tuple(c) for c in colors[4:]}) == 1
        # And the two polygons (domain extremes) resolve differently
        assert tuple(colors[0]) != tuple(colors[4])

    def test_callable_accessor_packs_per_vertex(self):
        from deckgl_marimo.layers._core import PolygonLayer

        data = [
            {"polygon": [[0, 0], [1, 0], [1, 1]], "v": 10},
            {"polygon": [[2, 2], [3, 2], [3, 3], [2, 3]], "v": 20},
        ]
        layer = PolygonLayer(
            data=data,
            get_polygon="polygon",
            get_fill_color=lambda row: [row["v"], 0, 0, 255],
            use_binary=True,
        )
        meta, buf = layer.to_binary()
        colors = self._unpack_colors(meta, buf, 7)
        assert [tuple(c) for c in colors[:3]] == [(10, 0, 0, 255)] * 3
        assert [tuple(c) for c in colors[3:]] == [(20, 0, 0, 255)] * 4

    def test_constant_color_omits_binary_colors(self):
        from deckgl_marimo.layers._core import PolygonLayer

        data = [{"polygon": [[0, 0], [1, 0], [1, 1]]}]
        layer = PolygonLayer(
            data=data,
            get_polygon="polygon",
            get_fill_color=[10, 20, 30, 255],
            use_binary=True,
        )
        meta, _buf = layer.to_binary()
        assert "getFillColor" not in meta["attributes"]
        # The constant stays in the spec for deck.gl to apply uniformly
        assert layer.to_spec()["getFillColor"] == [10, 20, 30, 255]
