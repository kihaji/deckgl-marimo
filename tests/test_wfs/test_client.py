"""Tests for WFSClient with a fake session (fixtures recorded from GeoServer 2.27.1)."""

import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from deckgl_marimo.wfs import Capabilities, WFSClient, WFSError, parse_describe_feature_type

FIX = Path(__file__).parent / "fixtures"
URL = "http://localhost:8080/geoserver/wfs"


class FakeResponse:
    def __init__(self, content: bytes, status_code: int = 200):
        self.content = content
        self.status_code = status_code


class FakeSession:
    """Routes requests to canned responses; records every call."""

    def __init__(self):
        self.calls: list[dict] = []
        self.routes: list[tuple] = []  # (predicate(method, url, kwargs) -> bool, response)

    def when(self, predicate, body: bytes, status: int = 200):
        self.routes.append((predicate, FakeResponse(body, status)))
        return self

    def request(self, method, url, **kwargs):
        self.calls.append({"method": method, "url": url, **kwargs})
        for pred, resp in self.routes:
            if pred(method, url, kwargs):
                return resp
        raise AssertionError(f"unexpected request {method} {url}")


def _q(url: str) -> dict[str, str]:
    return {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}


def _is(request: str):
    return lambda m, url, kw: _q(url).get("REQUEST") == request


class TestCapabilities:
    @pytest.mark.parametrize("version, vtag", [("2.0.0", "200"), ("1.1.0", "110"), ("1.0.0", "100")])
    def test_parses_feature_types_and_operations(self, version, vtag):
        s = FakeSession().when(_is("GetCapabilities"), (FIX / f"capabilities_{vtag}.xml").read_bytes())
        caps = WFSClient(URL, version=version, session=s).get_capabilities()
        assert isinstance(caps, Capabilities)
        assert caps.version == version
        assert "topp:tasmania_roads" in caps.feature_types
        assert "topp:states" in caps.feature_types
        assert len(caps.feature_types) == 19
        assert caps.supports_transaction
        assert {"GetCapabilities", "DescribeFeatureType", "GetFeature", "Transaction"} <= set(caps.operations)
        q = _q(s.calls[0]["url"])
        assert q == {"SERVICE": "WFS", "VERSION": version, "REQUEST": "GetCapabilities"}

    def test_title_and_no_transaction(self):
        body = (
            b'<wfs:WFS_Capabilities version="2.0.0" xmlns:wfs="http://www.opengis.net/wfs/2.0" xmlns:ows="http://www.opengis.net/ows/1.1">'
            b"<ows:ServiceIdentification><ows:Title>My WFS</ows:Title></ows:ServiceIdentification>"
            b'<ows:OperationsMetadata><ows:Operation name="GetFeature"/></ows:OperationsMetadata>'
            b"<wfs:FeatureTypeList><wfs:FeatureType><wfs:Name>a:b</wfs:Name></wfs:FeatureType></wfs:FeatureTypeList>"
            b"</wfs:WFS_Capabilities>"
        )
        caps = WFSClient(URL, session=FakeSession().when(_is("GetCapabilities"), body)).get_capabilities()
        assert caps.title == "My WFS"
        assert caps.feature_types == ["a:b"]
        assert caps.supports_transaction is False


class TestDescribeFeatureType:
    def test_parses_geometry_and_properties_200(self):
        s = FakeSession().when(_is("DescribeFeatureType"), (FIX / "describe_tasmania_roads_200.xsd").read_bytes())
        c = WFSClient(URL, session=s)
        info = c.describe_feature_type("topp:tasmania_roads")
        assert info.prefix == "topp"
        assert info.local_name == "tasmania_roads"
        assert info.namespace == "http://www.openplans.org/topp"
        assert info.geometry_name == "the_geom"
        assert info.geometry_type == "MultiLineString"  # MultiCurvePropertyType normalised
        assert info.properties == {"TYPE": "xsd:string"}
        assert _q(s.calls[0]["url"])["typeNames"] == "topp:tasmania_roads"
        # cached
        c.describe_feature_type("topp:tasmania_roads")
        assert len(s.calls) == 1

    def test_110_uses_typename_param(self):
        s = FakeSession().when(_is("DescribeFeatureType"), (FIX / "describe_tasmania_roads_110.xsd").read_bytes())
        info = WFSClient(URL, version="1.1.0", session=s).describe_feature_type("topp:tasmania_roads")
        assert info.geometry_type == "MultiLineString"
        assert _q(s.calls[0]["url"])["typeName"] == "topp:tasmania_roads"

    def test_point_type_and_several_properties(self):
        info = parse_describe_feature_type((FIX / "describe_bugsites_200.xsd").read_bytes(), "sf:bugsites")
        assert info.geometry_type == "Point"
        assert info.properties == {"cat": "xsd:long", "str1": "xsd:string"}

    def test_unqualified_typename_recovers_prefix_from_xmlns(self):
        info = parse_describe_feature_type((FIX / "describe_bugsites_200.xsd").read_bytes(), "bugsites")
        assert info.prefix == "sf"
        assert info.local_name == "bugsites"
        assert info.namespace == "http://www.openplans.org/spearfish"

    def test_unknown_element_raises(self):
        with pytest.raises(WFSError, match="does not declare element"):
            parse_describe_feature_type((FIX / "describe_bugsites_200.xsd").read_bytes(), "sf:other")

    def test_exception_report_raises(self):
        s = FakeSession().when(_is("DescribeFeatureType"), (FIX / "exception_ows_200.xml").read_bytes())
        with pytest.raises(WFSError, match="InvalidParameterValue"):
            WFSClient(URL, session=s).describe_feature_type("topp:nope")


class TestGetFeatures:
    def test_returns_feature_collection_and_builds_url(self):
        s = FakeSession().when(_is("GetFeature"), (FIX / "getfeature_tasmania_roads.json").read_bytes())
        c = WFSClient(URL, session=s, headers={"X-Token": "t"}, auth=("u", "p"), timeout=5)
        fc = c.get_features("topp:tasmania_roads", bbox=((140, -45), (150, -40)), max_features=2)
        assert fc["type"] == "FeatureCollection"
        assert fc["features"][0]["id"] == "tasmania_roads.1"
        call = s.calls[0]
        assert call["method"] == "GET"
        q = _q(call["url"])
        assert q["typeNames"] == "topp:tasmania_roads"
        assert q["BBOX"] == "140.0,-45.0,150.0,-40.0,EPSG:4326"
        assert q["count"] == "2"
        assert call["headers"] == {"X-Token": "t"}
        assert call["auth"] == ("u", "p")
        assert call["timeout"] == 5

    def test_non_json_raises(self):
        s = FakeSession().when(_is("GetFeature"), b"<wfs:FeatureCollection xmlns:wfs='x'/>")
        with pytest.raises(WFSError, match="did not return JSON"):
            WFSClient(URL, session=s).get_features("a:b")

    def test_http_error_raises(self):
        s = FakeSession().when(_is("GetFeature"), b"Unauthorized", 401)
        with pytest.raises(WFSError, match="HTTP 401") as ei:
            WFSClient(URL, session=s).get_features("a:b")
        assert ei.value.status == 401

    def test_transport_error_wrapped(self):
        class Boom:
            def request(self, *a, **k):
                raise ConnectionError("refused")

        with pytest.raises(WFSError, match="refused"):
            WFSClient(URL, session=Boom()).get_features("a:b")

    def test_get_feature_url_helper(self):
        url = WFSClient(URL + "?authkey=k", version="1.1.0").get_feature_url("a:b", max_features=1)
        q = _q(url)
        assert q["typeName"] == "a:b" and q["maxFeatures"] == "1" and q["authkey"] == "k"


class TestTransaction:
    def _client(self, version="2.0.0", **kw):
        vtag = version.replace(".", "")
        s = (
            FakeSession()
            .when(_is("DescribeFeatureType"), (FIX / f"describe_tasmania_roads_{'200' if version == '2.0.0' else '110'}.xsd").read_bytes())
            .when(lambda m, u, k: m == "POST", (FIX / f"txresponse_insert_{vtag}.xml").read_bytes())
        )
        return WFSClient(URL, version=version, session=s, auth=("admin", "geoserver"), **kw), s

    def test_insert_posts_xml_and_parses_result(self):
        c, s = self._client()
        feature = {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": [[146.0, -42.0], [146.5, -42.2]]},
            "properties": {"TYPE": "dgl"},
        }
        result = c.insert("topp:tasmania_roads", feature)
        assert result.inserted == 1
        post = [call for call in s.calls if call["method"] == "POST"][0]
        assert post["url"] == URL
        assert post["headers"]["Content-Type"].startswith("text/xml")
        assert post["auth"] == ("admin", "geoserver")
        body = post["data"].decode()
        assert "<wfs:Insert><topp:tasmania_roads><topp:the_geom><gml:MultiCurve" in body
        assert "<gml:posList>-42 146 -42.2 146.5</gml:posList>" in body  # auto axis swap for urn srs

    def test_insert_accepts_feature_collection(self):
        c, s = self._client()
        c.insert("topp:tasmania_roads", {"type": "FeatureCollection", "features": [
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [1, 2]}, "properties": {}},
        ] * 0})
        assert not [call for call in s.calls if call["method"] == "POST"]  # empty -> no request

    def test_axis_order_xy_and_custom_srs(self):
        c, s = self._client(axis_order="xy", srs_name="EPSG:4326")
        c.update("topp:tasmania_roads", "tasmania_roads.1", geometry={"type": "LineString", "coordinates": [[146.0, -42.0], [146.5, -42.2]]})
        body = [call for call in s.calls if call["method"] == "POST"][0]["data"].decode()
        assert 'srsName="EPSG:4326"' in body
        assert "<gml:posList>146 -42 146.5 -42.2</gml:posList>" in body

    def test_geometry_mismatch_raises_before_post(self):
        c, s = self._client()
        with pytest.raises(WFSError, match="does not match"):
            c.update("topp:tasmania_roads", "r.1", geometry={"type": "Point", "coordinates": [1, 2]})
        assert not [call for call in s.calls if call["method"] == "POST"]

    def test_axis_order_auto_no_swap_for_epsg_code(self):
        c, _ = self._client(srs_name="EPSG:4326")
        assert c._write_srs() == ("EPSG:4326", False)
        c, _ = self._client()
        assert c._write_srs() == ("urn:ogc:def:crs:EPSG::4326", True)
        c, _ = self._client(version="1.1.0", axis_order="yx", srs_name="EPSG:4326")
        assert c._write_srs() == ("EPSG:4326", True)
        c, _ = self._client(version="1.0.0")
        assert c._write_srs() == ("EPSG:4326", False)

    def test_delete_and_update_110(self):
        c, s = self._client(version="1.1.0")
        c.delete("topp:tasmania_roads", ["tasmania_roads.3"])
        c.update("topp:tasmania_roads", "tasmania_roads.4", properties={"TYPE": "x"})
        posts = [call["data"].decode() for call in s.calls if call["method"] == "POST"]
        assert '<ogc:FeatureId fid="tasmania_roads.3"/>' in posts[0]
        assert "<wfs:Name>TYPE</wfs:Name>" in posts[1]

    def test_build_transaction_without_sending(self):
        c, s = self._client()
        xml = c.build_transaction("topp:tasmania_roads", deletes=["r.1"])
        assert b"<wfs:Delete" in xml
        assert not [call for call in s.calls if call["method"] == "POST"]

    def test_empty_transaction_is_noop(self):
        c, s = self._client()
        assert c.transaction("topp:tasmania_roads").total == 0
        assert s.calls == []

    def test_server_exception_on_post(self):
        s = (
            FakeSession()
            .when(_is("DescribeFeatureType"), (FIX / "describe_tasmania_roads_200.xsd").read_bytes())
            .when(lambda m, u, k: m == "POST", (FIX / "exception_ows_200.xml").read_bytes(), 200)
        )
        with pytest.raises(WFSError, match="InvalidParameterValue"):
            WFSClient(URL, session=s).delete("topp:tasmania_roads", "r.1")

    def test_unknown_property_update_raises_before_post(self):
        c, s = self._client()
        with pytest.raises(WFSError, match="nothing to apply"):
            c.update("topp:tasmania_roads", "r.1", properties={"NOPE": 1})
        assert not [call for call in s.calls if call["method"] == "POST"]


class TestConstructor:
    def test_bad_version_and_axis_order(self):
        with pytest.raises(ValueError):
            WFSClient(URL, version="9")
        with pytest.raises(ValueError):
            WFSClient(URL, axis_order="zz")

    def test_lazy_requests_session(self):
        c = WFSClient(URL)
        assert c._session is None
        sess = c._get_session()
        assert type(sess).__name__ == "Session"
        assert c._get_session() is sess


def test_getfeature_fixture_is_geoserver_json():
    data = json.loads((FIX / "getfeature_tasmania_roads.json").read_text())
    assert data["features"][0]["geometry_name"] == "the_geom"
