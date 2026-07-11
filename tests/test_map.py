"""Tests for Map widget."""

import pytest

from deckgl_marimo._map import Map
from deckgl_marimo._base import BaseLayer
from deckgl_marimo.layers._core import ScatterplotLayer
from deckgl_marimo.layers._aggregation import HexagonLayer


class TestMapConstruction:
    def test_empty_map(self):
        m = Map()
        assert m.layer_specs == []
        assert m.zoom == 1.0
        assert m.pitch == 0.0

    def test_map_with_layers(self):
        layer = ScatterplotLayer(
            data=[{"lon": 1, "lat": 2}],
            get_position=["lon", "lat"],
        )
        m = Map(layers=[layer])
        assert len(m.layer_specs) == 1
        assert m.layer_specs[0]["type"] == "ScatterplotLayer"

    def test_map_center(self):
        m = Map(center=(-122.4, 37.8))
        assert m.longitude == -122.4
        assert m.latitude == 37.8

    def test_map_view_state(self):
        m = Map(zoom=10, pitch=45, bearing=90)
        assert m.zoom == 10
        assert m.pitch == 45
        assert m.bearing == 90

    def test_map_basemap(self):
        m = Map(basemap="dark-matter")
        assert "cartocdn.com" in m.basemap_style

    def test_map_custom_basemap_url(self):
        url = "https://my-tiles.example.com/style.json"
        m = Map(basemap=url)
        assert m.basemap_style == url

    def test_map_layout(self):
        m = Map(height="800px", width="50%")
        assert m.height == "800px"
        assert m.width == "50%"


class TestMapLayerManagement:
    def test_add_layer(self):
        m = Map()
        layer = ScatterplotLayer(data=[{"lon": 1, "lat": 2}], get_position=["lon", "lat"])
        m.add_layer(layer)
        assert len(m.layer_specs) == 1

    def test_remove_layer(self):
        layer = ScatterplotLayer(id="test-layer", data=[{"lon": 1, "lat": 2}], get_position=["lon", "lat"])
        m = Map(layers=[layer])
        m.remove_layer("test-layer")
        assert len(m.layer_specs) == 0

    def test_update_layer(self):
        layer = ScatterplotLayer(
            id="test-layer",
            data=[{"lon": 1, "lat": 2}],
            get_position=["lon", "lat"],
            opacity=0.5,
        )
        m = Map(layers=[layer])
        m.update_layer("test-layer", opacity=1.0)
        assert m.layer_specs[0]["opacity"] == 1.0

    def test_update_layer_min_max_zoom(self):
        layer = ScatterplotLayer(
            id="test-layer",
            data=[{"lon": 1, "lat": 2}],
            get_position=["lon", "lat"],
        )
        m = Map(layers=[layer])
        assert "minZoom" not in m.layer_specs[0]
        m.update_layer("test-layer", min_zoom=10, max_zoom=16)
        assert m.layer_specs[0]["minZoom"] == 10
        assert m.layer_specs[0]["maxZoom"] == 16

    def test_layers_property(self):
        layer = ScatterplotLayer(data=[{"lon": 1, "lat": 2}], get_position=["lon", "lat"])
        m = Map(layers=[layer])
        assert len(m.layers) == 1
        # Should be a copy
        m.layers.append(BaseLayer())
        assert len(m.layers) == 1

    def test_multi_layer(self):
        scatter = ScatterplotLayer(data=[{"lon": 1, "lat": 2}], get_position=["lon", "lat"])
        hexagon = HexagonLayer(data=[{"lon": 1, "lat": 2}], get_position=["lon", "lat"])
        m = Map(layers=[scatter, hexagon])
        assert len(m.layer_specs) == 2
        types = [s["type"] for s in m.layer_specs]
        assert "ScatterplotLayer" in types
        assert "HexagonLayer" in types


class TestAsWidgetWithoutMarimo:
    def test_helpful_error_when_marimo_missing(self, monkeypatch):
        import sys

        from deckgl_marimo import Map

        m = Map()
        # Setting a module's sys.modules entry to None makes `import marimo`
        # raise ImportError, simulating an environment without the extra.
        monkeypatch.setitem(sys.modules, "marimo", None)
        with pytest.raises(ImportError, match=r"deckgl-marimo\[marimo\]"):
            m.as_widget()
