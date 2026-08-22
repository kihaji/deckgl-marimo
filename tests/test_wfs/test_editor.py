"""Tests for WFSEditor / diff_features (no network: stub client + real Map)."""

import copy

import pytest

from deckgl_marimo import EMPTY_FEATURE_COLLECTION, DrawingStyle, Map
from deckgl_marimo.wfs import ChangeSet, TransactionResult, WFSEditor, diff_features


def feat(fid, coords, **props):
    return {
        "type": "Feature",
        "id": fid,
        "geometry": {"type": "Point", "coordinates": list(coords)},
        "properties": dict(props),
    }


def fc(*features):
    return {"type": "FeatureCollection", "features": list(features)}


class StubClient:
    def __init__(self, features=None, inserted_ids=None):
        self.features = features if features is not None else [feat("t.1", (1, 1), name="a"), feat("t.2", (2, 2), name="b")]
        self.inserted_ids = inserted_ids
        self.get_calls: list[dict] = []
        self.tx_calls: list[dict] = []

    def get_features(self, typename, **query):
        self.get_calls.append({"typename": typename, **query})
        return copy.deepcopy(fc(*self.features))

    def transaction(self, typename, *, inserts=(), updates=(), deletes=()):
        self.tx_calls.append({"typename": typename, "inserts": list(inserts), "updates": list(updates), "deletes": list(deletes)})
        ids = self.inserted_ids if self.inserted_ids is not None else [f"t.new{i}" for i in range(len(inserts))]
        return TransactionResult(inserted=len(inserts), updated=len(updates), deleted=len(deletes), inserted_ids=ids)


class TestDiffFeatures:
    def test_no_changes(self):
        a = fc(feat("1", (0, 0), x=1))
        assert diff_features(a, copy.deepcopy(a)).is_empty()

    def test_insert_without_id_and_unknown_id(self):
        snap = fc(feat("1", (0, 0)))
        cur = fc(feat("1", (0, 0)), {"type": "Feature", "geometry": {"type": "Point", "coordinates": [5, 5]}, "properties": {}}, feat("zzz", (9, 9)))
        cs = diff_features(snap, cur)
        assert len(cs.inserts) == 2
        assert not cs.updates and not cs.deletes

    def test_delete(self):
        cs = diff_features(fc(feat("1", (0, 0)), feat("2", (1, 1))), fc(feat("2", (1, 1))))
        assert cs.deletes == ["1"]
        assert cs.is_empty() is False

    def test_geometry_update_only(self):
        cs = diff_features(fc(feat("1", (0, 0), a=1)), fc(feat("1", (0.5, 0), a=1)))
        assert len(cs.updates) == 1
        fid, change = cs.updates[0]
        assert fid == "1"
        assert change["geometry"] == {"type": "Point", "coordinates": [0.5, 0]}
        assert change["properties"] == {}

    def test_property_update_only_carries_changed_keys(self):
        cs = diff_features(fc(feat("1", (0, 0), a=1, b=2, d=4)), fc(feat("1", (0, 0), a=1, b=3, c=None, d=None)))
        fid, change = cs.updates[0]
        assert change["geometry"] is None
        # b changed, d was nulled; c is a new key with no value -> not a change
        assert change["properties"] == {"b": 3, "d": None}

    def test_float_noise_ignored(self):
        cs = diff_features(fc(feat("1", (0.1, 0.2))), fc(feat("1", (0.1 + 1e-12, 0.2))))
        assert cs.is_empty()

    def test_summary(self):
        cs = ChangeSet(inserts=[{}], deletes=["a", "b"])
        assert cs.summary() == "1 insert(s), 0 update(s), 2 delete(s)"


class TestWFSEditor:
    def test_load_sets_drawing_features_and_snapshot(self):
        m = Map()
        client = StubClient()
        editor = WFSEditor(m, client, "ns:t", bbox=((-10, -10), (10, 10)), cql_filter="x=1", max_features=50)
        n = editor.load()
        assert n == 2
        assert m.drawing_features["features"][1]["id"] == "t.2"
        assert editor.snapshot == m.drawing_features
        assert editor.snapshot is not m.drawing_features  # independent copies
        q = client.get_calls[0]
        assert q == {"typename": "ns:t", "max_features": 50, "srs": "EPSG:4326", "bbox": ((-10, -10), (10, 10)), "cql_filter": "x=1"}

    def test_load_warns_when_truncated(self):
        m = Map()
        editor = WFSEditor(m, StubClient(), "ns:t", max_features=2)
        with pytest.warns(UserWarning, match="max_features"):
            editor.load()

    def test_changes_after_simulated_js_edits(self):
        m = Map()
        editor = WFSEditor(m, StubClient(), "ns:t")
        editor.load()
        current = copy.deepcopy(m.drawing_features)
        current["features"][0]["geometry"]["coordinates"] = [1.5, 1]        # modify t.1
        del current["features"][1]                                           # delete t.2
        current["features"].append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [7, 7]}, "properties": {"name": "new"}})
        m.drawing_features = current                                          # what the frontend does
        cs = editor.changes()
        assert [u[0] for u in cs.updates] == ["t.1"]
        assert cs.deletes == ["t.2"]
        assert len(cs.inserts) == 1
        assert cs.summary() == "1 insert(s), 1 update(s), 1 delete(s)"

    def test_commit_sends_one_transaction_and_reloads(self):
        m = Map()
        client = StubClient()
        editor = WFSEditor(m, client, "ns:t")
        editor.load()
        current = copy.deepcopy(m.drawing_features)
        current["features"][0]["properties"]["name"] = "changed"
        m.drawing_features = current
        client.features[0]["properties"]["name"] = "changed"  # server state after the tx
        result = editor.commit()
        assert result.updated == 1
        assert len(client.tx_calls) == 1
        assert client.tx_calls[0]["updates"] == [("t.1", {"geometry": None, "properties": {"name": "changed"}})]
        assert len(client.get_calls) == 2  # load + reload
        assert editor.changes().is_empty()

    def test_commit_without_changes_is_a_noop(self):
        m = Map()
        client = StubClient()
        editor = WFSEditor(m, client, "ns:t")
        editor.load()
        assert editor.commit().total == 0
        assert client.tx_calls == []

    def test_commit_without_reload_stamps_inserted_ids(self):
        m = Map()
        client = StubClient(inserted_ids=["t.77"])
        editor = WFSEditor(m, client, "ns:t")
        editor.load()
        current = copy.deepcopy(m.drawing_features)
        current["features"].append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [7, 7]}, "properties": {}})
        m.drawing_features = current
        editor.commit(reload=False)
        assert m.drawing_features["features"][-1]["id"] == "t.77"
        assert editor.changes().is_empty()
        assert len(client.get_calls) == 1

    def test_commit_without_reload_falls_back_when_ids_are_placeholders(self):
        # GeoServer returns rid="new0" for some stores (shapefile); those are not usable ids.
        m = Map()
        client = StubClient(inserted_ids=["new0"])
        editor = WFSEditor(m, client, "ns:t")
        editor.load()
        current = copy.deepcopy(m.drawing_features)
        current["features"].append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [7, 7]}, "properties": {}})
        m.drawing_features = current
        editor.commit(reload=False)
        assert len(client.get_calls) == 2  # reloaded anyway
        assert editor.changes().is_empty()

    def test_discard_restores_snapshot(self):
        m = Map()
        editor = WFSEditor(m, StubClient(), "ns:t")
        editor.load()
        m.drawing_features = fc()
        assert editor.changes().deletes == ["t.1", "t.2"]
        editor.discard()
        assert editor.changes().is_empty()
        assert len(m.drawing_features["features"]) == 2

    def test_update_properties_by_id_and_index(self):
        m = Map()
        editor = WFSEditor(m, StubClient(), "ns:t")
        editor.load()
        editor.update_properties("t.2", {"name": "B", "extra": 1})
        editor.update_properties(0, {"name": "A"})
        cs = editor.changes()
        assert sorted(u[0] for u in cs.updates) == ["t.1", "t.2"]
        assert dict(cs.updates)["t.2"]["properties"] == {"name": "B", "extra": 1}
        with pytest.raises(KeyError):
            editor.update_properties("nope", {})

    def test_set_mode_and_selection(self):
        m = Map()
        editor = WFSEditor(m, StubClient(), "ns:t", style=DrawingStyle(line_width=3))
        editor.load()
        editor.set_mode("modify", selected=["t.2", 0])
        assert m.drawing_config == {"mode": "modify", "selectedFeatureIndexes": [1, 0], "style": {"lineWidth": 3}}
        assert editor.index_of("t.2") == 1
        assert editor.index_of("missing") is None
        editor.delete_selected()
        assert m.drawing_config["deleteSelected"] is True
        assert m.drawing_config["mode"] == "modify"
        with pytest.raises(ValueError):
            editor.set_mode("scribble")

    def test_clear_empties_layer_but_keeps_snapshot(self):
        m = Map()
        editor = WFSEditor(m, StubClient(), "ns:t")
        editor.load()
        editor.clear()
        assert m.drawing_features == EMPTY_FEATURE_COLLECTION
        assert len(editor.snapshot["features"]) == 2
        assert editor.changes().deletes == ["t.1", "t.2"]
