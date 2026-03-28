"""Tests for core layer classes."""

from deckgl_marimo.layers._core import (
    ArcLayer,
    ColumnLayer,
    GeoJsonLayer,
    IconLayer,
    PathLayer,
    PolygonLayer,
    ScatterplotLayer,
    TextLayer,
)


class TestScatterplotLayer:
    def test_type(self):
        layer = ScatterplotLayer()
        assert layer.LAYER_TYPE == "ScatterplotLayer"

    def test_to_spec(self):
        layer = ScatterplotLayer(
            data=[{"lon": 1, "lat": 2}],
            get_position=["lon", "lat"],
            get_fill_color=[255, 0, 0],
            radius_scale=2,
        )
        spec = layer.to_spec()
        assert spec["type"] == "ScatterplotLayer"
        assert spec["getPosition"] == ["lon", "lat"]
        assert spec["getFillColor"] == [255, 0, 0]
        assert spec["radiusScale"] == 2
        assert spec["filled"] is True
        assert spec["stroked"] is False

    def test_default_colors_are_lists(self):
        layer = ScatterplotLayer()
        spec = layer.to_spec()
        assert isinstance(spec["getFillColor"], list)
        assert isinstance(spec["getLineColor"], list)


class TestGeoJsonLayer:
    def test_type(self):
        assert GeoJsonLayer().LAYER_TYPE == "GeoJsonLayer"

    def test_to_spec_with_geojson(self):
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [0, 0]},
                    "properties": {},
                }
            ],
        }
        layer = GeoJsonLayer(data=geojson)
        spec = layer.to_spec()
        assert spec["data"] == geojson
        assert spec["filled"] is True
        assert spec["stroked"] is True

    def test_to_spec_with_url(self):
        layer = GeoJsonLayer(data="https://example.com/data.geojson")
        spec = layer.to_spec()
        assert spec["data"] == "https://example.com/data.geojson"


class TestArcLayer:
    def test_type(self):
        assert ArcLayer().LAYER_TYPE == "ArcLayer"

    def test_to_spec(self):
        layer = ArcLayer(
            data=[{"src_lon": 0, "src_lat": 0, "dst_lon": 1, "dst_lat": 1}],
            get_source_position=["src_lon", "src_lat"],
            get_target_position=["dst_lon", "dst_lat"],
        )
        spec = layer.to_spec()
        assert spec["getSourcePosition"] == ["src_lon", "src_lat"]
        assert spec["getTargetPosition"] == ["dst_lon", "dst_lat"]


class TestPathLayer:
    def test_type(self):
        assert PathLayer().LAYER_TYPE == "PathLayer"

    def test_to_spec(self):
        layer = PathLayer(
            data=[{"path": [[0, 0], [1, 1]]}],
            get_path="path",
            get_color=[0, 255, 0],
            width_min_pixels=2,
        )
        spec = layer.to_spec()
        assert spec["getPath"] == "path"
        assert spec["getColor"] == [0, 255, 0]
        assert spec["widthMinPixels"] == 2


class TestPolygonLayer:
    def test_type(self):
        assert PolygonLayer().LAYER_TYPE == "PolygonLayer"

    def test_to_spec(self):
        layer = PolygonLayer(extruded=True, elevation_scale=10)
        spec = layer.to_spec()
        assert spec["extruded"] is True
        assert spec["elevationScale"] == 10


class TestIconLayer:
    def test_type(self):
        assert IconLayer().LAYER_TYPE == "IconLayer"

    def test_to_spec_with_atlas(self):
        layer = IconLayer(
            icon_atlas="https://example.com/atlas.png",
            icon_mapping={"marker": {"x": 0, "y": 0, "width": 128, "height": 128}},
        )
        spec = layer.to_spec()
        assert spec["iconAtlas"] == "https://example.com/atlas.png"
        assert "marker" in spec["iconMapping"]


class TestTextLayer:
    def test_type(self):
        assert TextLayer().LAYER_TYPE == "TextLayer"

    def test_to_spec(self):
        layer = TextLayer(get_text="label", get_size=16)
        spec = layer.to_spec()
        assert spec["getText"] == "label"
        assert spec["getSize"] == 16


class TestColumnLayer:
    def test_type(self):
        assert ColumnLayer().LAYER_TYPE == "ColumnLayer"

    def test_to_spec(self):
        layer = ColumnLayer(radius=500, elevation_scale=5)
        spec = layer.to_spec()
        assert spec["radius"] == 500
        assert spec["elevationScale"] == 5
        assert spec["extruded"] is True
