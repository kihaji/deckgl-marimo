"""Tests for composite layers."""

from deckgl_marimo._base import BaseLayer
from deckgl_marimo.layers._composite import DisplacementLayer
from deckgl_marimo.layers._core import ScatterplotLayer


SAMPLE_DATA = [
    {"lon": 1, "lat": 2, "rep_lon": 1.1, "rep_lat": 2.1},
    {"lon": 3, "lat": 4, "rep_lon": 3.2, "rep_lat": 4.2},
]


class TestBaseLayerToSpecs:
    def test_default_to_specs_wraps_to_spec(self):
        layer = ScatterplotLayer(data=SAMPLE_DATA, get_position=["lon", "lat"])
        specs = layer.to_specs()
        assert len(specs) == 1
        assert specs[0] == layer.to_spec()


class TestDisplacementLayer:
    def _make(self, **kwargs):
        defaults = dict(
            data=SAMPLE_DATA,
            origin=["lon", "lat"],
            displaced=["rep_lon", "rep_lat"],
        )
        defaults.update(kwargs)
        return DisplacementLayer(**defaults)

    def test_produces_three_specs_by_default(self):
        layer = self._make()
        specs = layer.to_specs()
        assert len(specs) == 3

    def test_spec_types(self):
        specs = self._make().to_specs()
        assert specs[0]["type"] == "ArcLayer"
        assert specs[1]["type"] == "ScatterplotLayer"
        assert specs[2]["type"] == "ScatterplotLayer"

    def test_sub_layer_ids(self):
        layer = self._make(id="test")
        specs = layer.to_specs()
        assert specs[0]["id"] == "test-arcs"
        assert specs[1]["id"] == "test-origin"
        assert specs[2]["id"] == "test-displaced"

    def test_hide_arcs(self):
        specs = self._make(show_arcs=False).to_specs()
        assert len(specs) == 2
        assert all(s["type"] == "ScatterplotLayer" for s in specs)

    def test_hide_origin_dots(self):
        specs = self._make(show_origin_dots=False).to_specs()
        assert len(specs) == 2
        assert specs[0]["type"] == "ArcLayer"
        assert specs[1]["id"].endswith("-displaced")

    def test_hide_displaced_dots(self):
        specs = self._make(show_displaced_dots=False).to_specs()
        assert len(specs) == 2
        assert specs[0]["type"] == "ArcLayer"
        assert specs[1]["id"].endswith("-origin")

    def test_hide_all(self):
        specs = self._make(
            show_arcs=False, show_origin_dots=False, show_displaced_dots=False
        ).to_specs()
        assert len(specs) == 0

    def test_to_spec_returns_first(self):
        layer = self._make()
        spec = layer.to_spec()
        assert spec["type"] == "ArcLayer"

    def test_to_spec_empty_when_all_hidden(self):
        layer = self._make(
            show_arcs=False, show_origin_dots=False, show_displaced_dots=False
        )
        assert layer.to_spec() == {}

    def test_arc_accessors(self):
        specs = self._make().to_specs()
        arc = specs[0]
        assert arc["getSourcePosition"] == ["lon", "lat"]
        assert arc["getTargetPosition"] == ["rep_lon", "rep_lat"]

    def test_scatter_accessors(self):
        specs = self._make().to_specs()
        origin = specs[1]
        displaced = specs[2]
        assert origin["getPosition"] == ["lon", "lat"]
        assert displaced["getPosition"] == ["rep_lon", "rep_lat"]

    def test_default_colors(self):
        specs = self._make().to_specs()
        arc = specs[0]
        assert arc["getSourceColor"] == [76, 175, 80, 200]
        assert arc["getTargetColor"] == [244, 67, 54, 200]
        origin = specs[1]
        assert origin["getFillColor"] == [76, 175, 80, 180]
        displaced = specs[2]
        assert displaced["getFillColor"] == [244, 67, 54, 180]

    def test_custom_colors(self):
        specs = self._make(
            arc_source_color=[0, 0, 255],
            origin_color=[0, 0, 200],
        ).to_specs()
        assert specs[0]["getSourceColor"] == [0, 0, 255]
        assert specs[1]["getFillColor"] == [0, 0, 200]

    def test_opacity_propagates(self):
        specs = self._make(opacity=0.5).to_specs()
        for spec in specs:
            assert spec["opacity"] == 0.5

    def test_pickable_propagates(self):
        specs = self._make(pickable=False).to_specs()
        for spec in specs:
            assert spec["pickable"] is False

    def test_data_on_all_specs(self):
        specs = self._make().to_specs()
        for spec in specs:
            assert spec["data"] == SAMPLE_DATA
