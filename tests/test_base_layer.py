"""Tests for BaseLayer and utility functions."""


import pytest
from deckgl_marimo._base import BaseLayer
from deckgl_marimo.layers._core import GeoJsonLayer
from deckgl_marimo._utils import to_camel_case


class TestToCamelCase:
    def test_single_word(self):
        assert to_camel_case("radius") == "radius"

    def test_two_words(self):
        assert to_camel_case("elevation_scale") == "elevationScale"

    def test_three_words(self):
        assert to_camel_case("get_fill_color") == "getFillColor"

    def test_already_camel(self):
        assert to_camel_case("radius") == "radius"


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
        layer = BaseLayer(visible_min_zoom=5)
        spec = layer.to_spec()
        assert spec["visibleMinZoom"] == 5

    def test_max_zoom_in_spec(self):
        layer = BaseLayer(visible_max_zoom=15)
        spec = layer.to_spec()
        assert spec["visibleMaxZoom"] == 15

    def test_both_zoom_bounds_in_spec(self):
        layer = BaseLayer(visible_min_zoom=5, visible_max_zoom=15)
        spec = layer.to_spec()
        assert spec["visibleMinZoom"] == 5
        assert spec["visibleMaxZoom"] == 15

    def test_no_zoom_keys_by_default(self):
        layer = BaseLayer()
        spec = layer.to_spec()
        assert "visibleMinZoom" not in spec
        assert "visibleMaxZoom" not in spec

    def test_fractional_zoom_bounds(self):
        layer = BaseLayer(visible_min_zoom=10.5, visible_max_zoom=14.25)
        spec = layer.to_spec()
        assert spec["visibleMinZoom"] == 10.5
        assert spec["visibleMaxZoom"] == 14.25


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


class TestZoomGatingRename:
    """visible_min_zoom/visible_max_zoom gating vs deck.gl zoom props (#22)."""

    def test_old_gating_names_raise_with_suggestion(self):
        from deckgl_marimo.layers._core import ScatterplotLayer

        with pytest.raises(TypeError, match="visible_min_zoom"):
            ScatterplotLayer(min_zoom=5)
        with pytest.raises(TypeError, match="visible_max_zoom"):
            ScatterplotLayer(max_zoom=15)

    def test_tile_layer_zoom_props_reach_the_spec(self):
        import warnings

        from deckgl_marimo.layers._geo import TileLayer

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # experimental warning
            layer = TileLayer(min_zoom=2, max_zoom=18)
        spec = layer.to_spec()
        # Real deck.gl tile-fetch bounds — no longer consumed by gating
        assert spec["minZoom"] == 2
        assert spec["maxZoom"] == 18
        assert "visibleMinZoom" not in spec

    def test_gating_and_tile_zoom_coexist(self):
        import warnings

        from deckgl_marimo.layers._geo import TileLayer

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            layer = TileLayer(min_zoom=2, max_zoom=18, visible_min_zoom=4)
        spec = layer.to_spec()
        assert spec["minZoom"] == 2
        assert spec["visibleMinZoom"] == 4
