"""Tests for picking resolution on binary-packed layers.

The JS side sends pick events with ``object: None`` whenever deck.gl
couldn't attach a data row (binary mode). The Map observer should look
up the original data by layer_id + index and fill in the row.
"""

from deckgl_marimo._map import Map
from deckgl_marimo.layers._core import ScatterplotLayer, PolygonLayer


def _pick(layer_id, index, object=None, coordinate=None):
    return {
        "object": object,
        "coordinate": coordinate or [0, 0],
        "layer_id": layer_id,
        "index": index,
    }


class TestBinaryPickResolution:
    def test_click_object_populated_from_data(self):
        layer = ScatterplotLayer(
            data=[
                {"lon": 1, "lat": 2, "name": "A"},
                {"lon": 3, "lat": 4, "name": "B"},
            ],
            get_position=["lon", "lat"],
            use_binary=True,
        )
        m = Map(layers=[layer])
        m.click_info = _pick(layer.id, 1)
        assert m.click_info["object"] == {"lon": 3, "lat": 4, "name": "B"}
        assert m.click_info["index"] == 1
        assert m.click_info["layer_id"] == layer.id

    def test_hover_object_populated_from_data(self):
        layer = ScatterplotLayer(
            data=[{"lon": 1, "lat": 2, "name": "A"}],
            get_position=["lon", "lat"],
            use_binary=True,
        )
        m = Map(layers=[layer])
        m.hover_info = _pick(layer.id, 0)
        assert m.hover_info["object"] == {"lon": 1, "lat": 2, "name": "A"}

    def test_json_mode_object_untouched(self):
        layer = ScatterplotLayer(
            data=[{"lon": 1, "lat": 2, "name": "A"}],
            get_position=["lon", "lat"],
        )
        m = Map(layers=[layer])
        prepopulated = {"lon": 1, "lat": 2, "name": "A", "extra": "js-computed"}
        m.click_info = _pick(layer.id, 0, object=prepopulated)
        # Observer must not overwrite an object the JS side already provided
        assert m.click_info["object"] is prepopulated

    def test_unknown_layer_id_noop(self):
        layer = ScatterplotLayer(
            data=[{"lon": 1, "lat": 2}],
            get_position=["lon", "lat"],
            use_binary=True,
        )
        m = Map(layers=[layer])
        m.click_info = _pick("does-not-exist", 0)
        assert m.click_info["object"] is None

    def test_out_of_range_index_noop(self):
        layer = ScatterplotLayer(
            data=[{"lon": 1, "lat": 2}],
            get_position=["lon", "lat"],
            use_binary=True,
        )
        m = Map(layers=[layer])
        m.click_info = _pick(layer.id, 99)
        assert m.click_info["object"] is None

    def test_negative_index_noop(self):
        layer = ScatterplotLayer(
            data=[{"lon": 1, "lat": 2}],
            get_position=["lon", "lat"],
            use_binary=True,
        )
        m = Map(layers=[layer])
        m.click_info = _pick(layer.id, -1)
        assert m.click_info["object"] is None

    def test_url_data_noop(self):
        # materialize_rows returns None for URL-backed data; observer must
        # not crash and must leave object as-is.
        layer = ScatterplotLayer(
            data="https://example.com/data.json",
            get_position=["lon", "lat"],
        )
        m = Map(layers=[layer])
        m.click_info = _pick(layer.id, 0)
        assert m.click_info["object"] is None

    def test_empty_pick_info_noop(self):
        m = Map()
        m.click_info = {}  # doesn't crash
        assert m.click_info == {}

    def test_observer_does_not_recurse(self):
        # Setting click_info inside the observer triggers another observe
        # call. The _resolving_pick flag should prevent infinite recursion.
        layer = ScatterplotLayer(
            data=[{"lon": 1, "lat": 2, "name": "A"}],
            get_position=["lon", "lat"],
            use_binary=True,
        )
        m = Map(layers=[layer])
        m.click_info = _pick(layer.id, 0)
        # If recursion occurred, we'd see a RecursionError above. Post-check:
        assert m.click_info["object"] == {"lon": 1, "lat": 2, "name": "A"}


class TestBinaryTooltipMetadata:
    def test_tooltip_column_packed_into_metadata(self):
        layer = ScatterplotLayer(
            data=[
                {"lon": 1, "lat": 2, "tooltip": "first"},
                {"lon": 3, "lat": 4, "tooltip": "second"},
            ],
            get_position=["lon", "lat"],
            use_binary=True,
        )
        m = Map(layers=[layer])
        meta = m.binary_metadata
        assert "layers" in meta
        layer_meta = meta["layers"][0]
        assert layer_meta.get("tooltips") == ["first", "second"]

    def test_no_tooltip_column_no_metadata(self):
        layer = ScatterplotLayer(
            data=[{"lon": 1, "lat": 2}],
            get_position=["lon", "lat"],
            use_binary=True,
        )
        m = Map(layers=[layer])
        layer_meta = m.binary_metadata["layers"][0]
        assert "tooltips" not in layer_meta
