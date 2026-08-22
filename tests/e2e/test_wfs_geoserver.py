"""Live WFS / WFS-T tests (opt-in: ``pytest --run-e2e tests/e2e``).

Read-only tests run against ``DECKGL_E2E_READ_URL`` if set, else the write
server below, else a public GeoServer (``https://ahocevar.com/geoserver/wfs``).

Write tests need a transactional server, e.g. the GeoServer docker image with
its sample data (``topp:tasmania_roads`` is a writable shapefile)::

    docker run -d --name geoserver -p 8080:8080 docker.osgeo.org/geoserver:2.27.1
    DECKGL_RUN_E2E=1 DECKGL_E2E_URL=http://localhost:8080/geoserver/wfs \\
        DECKGL_E2E_AUTH=admin:geoserver uv run pytest tests/e2e -v

Without ``DECKGL_E2E_URL`` the write tests are skipped.
"""

from __future__ import annotations

import os

import pytest

from deckgl_marimo import Map
from deckgl_marimo.wfs import WFSClient, WFSEditor, WFSError

pytestmark = pytest.mark.e2e

WRITE_URL = os.environ.get("DECKGL_E2E_URL")
# Reads default to the local server when one is configured (its sample data
# also has topp:states), otherwise to a public read-only GeoServer.
READ_URL = os.environ.get("DECKGL_E2E_READ_URL") or WRITE_URL or "https://ahocevar.com/geoserver/wfs"
READ_TYPE = os.environ.get("DECKGL_E2E_READ_TYPE", "topp:states")
WRITE_TYPE = os.environ.get("DECKGL_E2E_TYPE", "topp:tasmania_roads")
_auth = os.environ.get("DECKGL_E2E_AUTH", "admin:geoserver")
WRITE_AUTH = tuple(_auth.split(":", 1)) if ":" in _auth else None

# Values short enough for the sample shapefile's DBF field widths.
TAG, TAG_UPDATED = "dgl", "dglupd"


class TestRead:
    def test_capabilities_and_describe(self):
        c = WFSClient(READ_URL)
        caps = c.get_capabilities()
        assert READ_TYPE in caps.feature_types
        info = c.describe_feature_type(READ_TYPE)
        assert info.geometry_name
        assert info.properties

    def test_get_features_with_bbox_and_count(self):
        c = WFSClient(READ_URL)
        fc = c.get_features(READ_TYPE, max_features=5)
        assert fc["type"] == "FeatureCollection"
        assert 0 < len(fc["features"]) <= 5
        assert all(f.get("id") for f in fc["features"])
        inside = c.get_features(READ_TYPE, bbox=((-100, 30), (-95, 35)), max_features=50)
        assert len(inside["features"]) >= 1

    def test_cql_filter(self):
        c = WFSClient(READ_URL)
        fc = c.get_features(READ_TYPE, cql_filter="STATE_NAME = 'Texas'")
        assert [f["properties"]["STATE_NAME"] for f in fc["features"]] == ["Texas"]

    def test_bad_typename_raises(self):
        with pytest.raises(WFSError):
            WFSClient(READ_URL).describe_feature_type("topp:does_not_exist")


@pytest.fixture
def write_client(request) -> WFSClient:
    if not WRITE_URL:
        pytest.skip("set DECKGL_E2E_URL (and DECKGL_E2E_AUTH) to run write tests")
    c = WFSClient(WRITE_URL, version=request.param, auth=WRITE_AUTH)
    if not c.get_capabilities().supports_transaction:
        pytest.skip("server does not advertise Transaction")
    yield c
    # clean up anything this run left behind
    leftovers = [f["id"] for f in c.get_features(WRITE_TYPE, cql_filter=f"TYPE LIKE '{TAG}%'")["features"]]
    if leftovers:
        c.delete(WRITE_TYPE, leftovers)


@pytest.mark.parametrize("write_client", ["2.0.0", "1.1.0", "1.0.0"], indirect=True)
class TestWrite:
    def test_insert_update_delete_round_trip(self, write_client: WFSClient):
        c = write_client
        info = c.describe_feature_type(WRITE_TYPE)
        assert info.geometry_type == "MultiLineString"
        before = len(c.get_features(WRITE_TYPE)["features"])

        line = {"type": "LineString", "coordinates": [[146.0, -42.0], [146.5, -42.2]]}
        res = c.insert(WRITE_TYPE, {"type": "Feature", "geometry": line, "properties": {"TYPE": TAG, "shape": "junk"}})
        assert res.inserted == 1 and len(res.inserted_ids) == 1

        created = c.get_features(WRITE_TYPE, cql_filter=f"TYPE = '{TAG}'")["features"]
        assert len(created) == 1
        fid = created[0]["id"]
        coords = created[0]["geometry"]["coordinates"][0][0]
        assert abs(coords[0] - 146.0) < 1e-6 and abs(coords[1] + 42.0) < 1e-6  # lon/lat preserved (axis order!)
        assert created[0]["geometry"]["type"] == "MultiLineString"  # promoted

        new_line = {"type": "LineString", "coordinates": [[147.0, -43.0], [147.5, -43.2]]}
        res = c.update(WRITE_TYPE, fid, geometry=new_line, properties={"TYPE": TAG_UPDATED})
        if c.version != "1.0.0":
            assert res.updated == 1
        after = c.get_features(WRITE_TYPE, feature_ids=[fid])["features"][0]
        assert after["properties"]["TYPE"] == TAG_UPDATED
        assert abs(after["geometry"]["coordinates"][0][0][0] - 147.0) < 1e-6

        res = c.delete(WRITE_TYPE, fid)
        if c.version != "1.0.0":
            assert res.deleted == 1
        assert len(c.get_features(WRITE_TYPE)["features"]) == before

    def test_unauthenticated_write_is_rejected(self, write_client: WFSClient):
        anon = WFSClient(write_client.url, version=write_client.version)
        with pytest.raises(WFSError):
            anon.delete(WRITE_TYPE, "tasmania_roads.999999")


@pytest.mark.parametrize("write_client", ["2.0.0"], indirect=True)
class TestEditorRoundTrip:
    def test_editor_commit_and_reload(self, write_client: WFSClient):
        m = Map()
        editor = WFSEditor(m, write_client, WRITE_TYPE, max_features=500)
        n = editor.load()
        assert n > 0 and len(m.drawing_features["features"]) == n

        # simulate the frontend: draw one, move one, delete one
        fc = dict(m.drawing_features)
        feats = list(fc["features"])
        moved_id = feats[0]["id"]
        moved = dict(feats[0])
        moved["geometry"] = {"type": "MultiLineString", "coordinates": [[[147.0, -43.0], [147.5, -43.2]]]}
        deleted_id = feats[1]["id"]
        new = {"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[146.0, -42.0], [146.5, -42.2]]},
               "properties": {"TYPE": TAG}}
        m.drawing_features = {"type": "FeatureCollection", "features": [moved, *feats[2:], new]}
        cs = editor.changes()
        assert [u[0] for u in cs.updates] == [moved_id] and cs.deletes == [deleted_id] and len(cs.inserts) == 1

        deleted_feature = feats[1]
        try:
            result = editor.commit()
            assert result.inserted == 1 and result.updated == 1 and result.deleted == 1
            assert editor.changes().is_empty()
            ids = {f["id"] for f in m.drawing_features["features"]}
            assert deleted_id not in ids
            assert any(f["properties"].get("TYPE") == TAG for f in m.drawing_features["features"])
        finally:
            # restore the sample data: re-insert the deleted feature, revert the moved one
            write_client.insert(WRITE_TYPE, {"type": "Feature", "geometry": deleted_feature["geometry"],
                                             "properties": deleted_feature["properties"]})
            write_client.update(WRITE_TYPE, moved_id, geometry=feats[0]["geometry"])
