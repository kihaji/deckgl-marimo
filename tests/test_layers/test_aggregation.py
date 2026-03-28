"""Tests for aggregation layer classes."""

from deckgl_marimo.layers._aggregation import HexagonLayer, HeatmapLayer


class TestHexagonLayer:
    def test_type(self):
        assert HexagonLayer().LAYER_TYPE == "HexagonLayer"

    def test_to_spec(self):
        layer = HexagonLayer(
            data=[{"lon": 1, "lat": 2}],
            get_position=["lon", "lat"],
            radius=2000,
            extruded=True,
            elevation_scale=250,
            coverage=0.8,
        )
        spec = layer.to_spec()
        assert spec["type"] == "HexagonLayer"
        assert spec["radius"] == 2000
        assert spec["extruded"] is True
        assert spec["elevationScale"] == 250
        assert spec["coverage"] == 0.8
        assert spec["getPosition"] == ["lon", "lat"]

    def test_default_color_range(self):
        layer = HexagonLayer()
        spec = layer.to_spec()
        assert len(spec["colorRange"]) == 6

    def test_custom_color_range(self):
        colors = [[0, 0, 0], [255, 255, 255]]
        layer = HexagonLayer(color_range=colors)
        spec = layer.to_spec()
        assert spec["colorRange"] == colors


class TestHeatmapLayer:
    def test_type(self):
        assert HeatmapLayer().LAYER_TYPE == "HeatmapLayer"

    def test_to_spec(self):
        layer = HeatmapLayer(
            data=[{"lon": 1, "lat": 2}],
            get_position=["lon", "lat"],
            radius_pixels=50,
            intensity=2,
            threshold=0.1,
        )
        spec = layer.to_spec()
        assert spec["type"] == "HeatmapLayer"
        assert spec["radiusPixels"] == 50
        assert spec["intensity"] == 2
        assert spec["threshold"] == 0.1
