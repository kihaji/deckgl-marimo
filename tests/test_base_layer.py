"""Tests for BaseLayer and utility functions."""

from deckgl_marimo._base import BaseLayer
from deckgl_marimo.layers._core import GeoJsonLayer
from deckgl_marimo._utils import to_camel_case, to_snake_case


class TestToCamelCase:
    def test_single_word(self):
        assert to_camel_case("radius") == "radius"

    def test_two_words(self):
        assert to_camel_case("elevation_scale") == "elevationScale"

    def test_three_words(self):
        assert to_camel_case("get_fill_color") == "getFillColor"

    def test_already_camel(self):
        assert to_camel_case("radius") == "radius"


class TestToSnakeCase:
    def test_camel(self):
        assert to_snake_case("elevationScale") == "elevation_scale"

    def test_get_prefix(self):
        assert to_snake_case("getFillColor") == "get_fill_color"

    def test_single_word(self):
        assert to_snake_case("radius") == "radius"


class TestBaseLayer:
    def test_to_spec_basic(self):
        layer = BaseLayer(visible=True, opacity=0.5)
        spec = layer.to_spec()
        assert spec["type"] == "BaseLayer"
        assert spec["visible"] is True
        assert spec["opacity"] == 0.5
        assert spec["pickable"] is True
        assert "id" in spec

    def test_to_spec_with_data(self):
        data = [{"x": 1, "y": 2}]
        layer = BaseLayer(data=data)
        spec = layer.to_spec()
        assert spec["data"] == data

    def test_to_spec_camel_case_props(self):
        layer = BaseLayer(elevation_scale=100, color_range=[[1, 2, 3]])
        spec = layer.to_spec()
        assert spec["elevationScale"] == 100
        assert spec["colorRange"] == [[1, 2, 3]]

    def test_custom_id(self):
        layer = BaseLayer(id="my-layer")
        assert layer.id == "my-layer"
        assert layer.to_spec()["id"] == "my-layer"

    def test_auto_id(self):
        layer = BaseLayer()
        assert layer.id.startswith("BaseLayer-")

    def test_no_data_in_spec_when_none(self):
        layer = BaseLayer()
        spec = layer.to_spec()
        assert "data" not in spec

    def test_repr(self):
        layer = BaseLayer(id="test-layer")
        assert repr(layer) == "BaseLayer(id='test-layer')"


class TestZoomVisibility:
    def test_min_zoom_in_spec(self):
        layer = BaseLayer(min_zoom=5)
        spec = layer.to_spec()
        assert spec["minZoom"] == 5

    def test_max_zoom_in_spec(self):
        layer = BaseLayer(max_zoom=15)
        spec = layer.to_spec()
        assert spec["maxZoom"] == 15

    def test_both_zoom_bounds_in_spec(self):
        layer = BaseLayer(min_zoom=5, max_zoom=15)
        spec = layer.to_spec()
        assert spec["minZoom"] == 5
        assert spec["maxZoom"] == 15

    def test_no_zoom_keys_by_default(self):
        layer = BaseLayer()
        spec = layer.to_spec()
        assert "minZoom" not in spec
        assert "maxZoom" not in spec

    def test_fractional_zoom_bounds(self):
        layer = BaseLayer(min_zoom=10.5, max_zoom=14.25)
        spec = layer.to_spec()
        assert spec["minZoom"] == 10.5
        assert spec["maxZoom"] == 14.25


class TestLoadOptions:
    def test_load_options_in_spec(self):
        opts = {"fetch": {"headers": {"Authorization": "Bearer xyz"}}}
        layer = BaseLayer(data="https://example.com/data.json", load_options=opts)
        spec = layer.to_spec()
        assert spec["loadOptions"] == opts

    def test_fetch_headers_convenience(self):
        layer = BaseLayer(
            data="https://example.com/data.json",
            fetch_headers={"Authorization": "Bearer xyz"},
        )
        spec = layer.to_spec()
        assert spec["loadOptions"] == {
            "fetch": {"headers": {"Authorization": "Bearer xyz"}}
        }

    def test_fetch_headers_merged_with_load_options(self):
        layer = BaseLayer(
            data="https://example.com/data.json",
            fetch_headers={"X-Default": "default-val", "Authorization": "from-headers"},
            load_options={
                "fetch": {
                    "credentials": "include",
                    "headers": {"Authorization": "from-load-options"},
                }
            },
        )
        spec = layer.to_spec()
        lo = spec["loadOptions"]
        assert lo["fetch"]["credentials"] == "include"
        # load_options headers take precedence over fetch_headers
        assert lo["fetch"]["headers"]["Authorization"] == "from-load-options"
        # fetch_headers defaults still present
        assert lo["fetch"]["headers"]["X-Default"] == "default-val"

    def test_no_load_options_when_none(self):
        layer = BaseLayer(data="https://example.com/data.json")
        spec = layer.to_spec()
        assert "loadOptions" not in spec

    def test_load_options_credentials(self):
        layer = BaseLayer(
            data="https://example.com/data.json",
            load_options={"fetch": {"credentials": "include"}},
        )
        spec = layer.to_spec()
        assert spec["loadOptions"]["fetch"]["credentials"] == "include"

    def test_load_options_with_geojson_layer(self):
        layer = GeoJsonLayer(
            data="https://example.com/data.geojson",
            fetch_headers={"X-API-Key": "abc123"},
        )
        spec = layer.to_spec()
        assert spec["type"] == "GeoJsonLayer"
        assert spec["loadOptions"] == {
            "fetch": {"headers": {"X-API-Key": "abc123"}}
        }
