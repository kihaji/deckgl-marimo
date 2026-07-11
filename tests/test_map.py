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
        assert "visibleMinZoom" not in m.layer_specs[0]
        m.update_layer("test-layer", visible_min_zoom=10, visible_max_zoom=16)
        assert m.layer_specs[0]["visibleMinZoom"] == 10
        assert m.layer_specs[0]["visibleMaxZoom"] == 16

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


class TestUpdateLayerRouting:
    """update_layer routes explicitly and never touches the backing Map (#20)."""

    def _map_with_layer(self):
        layer = ScatterplotLayer(
            id="pts", data=[{"lon": 0, "lat": 0}], get_position=["lon", "lat"]
        )
        return Map(layers=[layer]), layer

    def test_spec_prop_roundtrips_into_to_spec(self):
        m, layer = self._map_with_layer()
        m.update_layer("pts", get_radius=42, radius_scale=2)
        spec = layer.to_spec()
        assert spec["getRadius"] == 42
        assert spec["radiusScale"] == 2

    def test_base_field_roundtrips_into_to_spec(self):
        m, layer = self._map_with_layer()
        m.update_layer("pts", visible=False, opacity=0.25)
        assert layer.visible is False
        spec = layer.to_spec()
        assert spec["visible"] is False
        assert spec["opacity"] == 0.25

    def test_never_instantiates_backing_map(self):
        m, layer = self._map_with_layer()
        m.update_layer("pts", get_radius=1, visible=True, opacity=0.5)
        assert layer._BaseLayer__map is None

    def test_unknown_prop_raises_with_suggestion(self):
        m, _layer = self._map_with_layer()
        with pytest.raises(TypeError, match="get_radius"):
            m.update_layer("pts", get_radiuss=5)

    def test_map_level_key_raises_helpful_error(self):
        m, layer = self._map_with_layer()
        with pytest.raises(ValueError, match="map-level"):
            m.update_layer("pts", zoom=10)
        # and no dead attribute was set on the layer
        assert "zoom" not in layer.__dict__

    def test_missing_layer_is_a_noop(self):
        m, _layer = self._map_with_layer()
        m.update_layer("nope", get_radius=5)  # no raise, no change


class TestSetLayers:
    """set_layers replaces layers and re-packs binary in one shot (#30)."""

    def test_replaces_specs_and_binary(self):
        np = pytest.importorskip("numpy")
        m = Map()
        assert m.layer_specs == []
        layer = ScatterplotLayer(
            id="bin",
            data=[{"lon": 1.0, "lat": 2.0}, {"lon": 3.0, "lat": 4.0}],
            get_position=["lon", "lat"],
            use_binary=True,
        )
        m.set_layers([layer])
        assert [s["id"] for s in m.layer_specs] == ["bin"]
        assert m.binary_metadata["layers"][0]["id"] == "bin"
        assert len(m.binary_data) > 0
        pos = np.frombuffer(m.binary_data[:16], dtype=np.float32)
        assert list(pos) == [1.0, 2.0, 3.0, 4.0]

    def test_replaces_existing_layers(self):
        a = ScatterplotLayer(id="a", data=[{"lon": 0, "lat": 0}], get_position=["lon", "lat"])
        b = ScatterplotLayer(id="b", data=[{"lon": 1, "lat": 1}], get_position=["lon", "lat"])
        m = Map(layers=[a])
        m.set_layers([b])
        assert [lyr.id for lyr in m.layers] == ["b"]
        assert [s["id"] for s in m.layer_specs] == ["b"]


class TestPromotedCoreLayers:
    """Line/PointCloud/SolidPolygon are core — no experimental warning (#28)."""

    def test_no_warning_on_construction(self):
        import warnings

        from deckgl_marimo import LineLayer, PointCloudLayer, SolidPolygonLayer

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            LineLayer()
            PointCloudLayer()
            SolidPolygonLayer()

    def test_pack_binary_public(self):
        import deckgl_marimo as dgl

        assert dgl.pack_binary is not None
        assert dgl.pack_polygon_binary is not None
        assert "pack_binary" in dgl.__all__


class TestPickRowCache:
    """Pick resolution caches materialized rows per layer (#23)."""

    def test_materializes_once_per_layer(self, monkeypatch):
        import deckgl_marimo._map as map_mod

        layer = ScatterplotLayer(
            id="pts", data=[{"lon": 0, "lat": 0, "name": "a"}, {"lon": 1, "lat": 1, "name": "b"}],
            get_position=["lon", "lat"],
        )
        m = Map(layers=[layer])
        calls = {"n": 0}
        real = map_mod.materialize_rows

        def counting(data):
            calls["n"] += 1
            return real(data)

        monkeypatch.setattr(map_mod, "materialize_rows", counting)
        for i in (0, 1, 0):
            m.click_info = {"object": None, "layer_id": "pts", "index": i, "coordinate": [0, 0]}
            assert m.click_info["object"]["name"] == ("a" if i == 0 else "b")
        assert calls["n"] == 1

    def test_cache_invalidated_on_layer_update(self):

        layer = ScatterplotLayer(
            id="pts", data=[{"lon": 0, "lat": 0, "name": "a"}], get_position=["lon", "lat"]
        )
        m = Map(layers=[layer])
        m.click_info = {"object": None, "layer_id": "pts", "index": 0, "coordinate": [0, 0]}
        assert m.click_info["object"]["name"] == "a"

        m.update_layer("pts", data=[{"lon": 0, "lat": 0, "name": "z"}])
        m.click_info = {"object": None, "layer_id": "pts", "index": 0, "coordinate": [0, 0]}
        assert m.click_info["object"]["name"] == "z"
