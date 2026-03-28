"""Tests for BaseLayer and utility functions."""

from deckgl_marimo._base import BaseLayer
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
