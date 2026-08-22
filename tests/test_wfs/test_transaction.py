"""Tests for the WFS-T Transaction XML builder and response parser.

Response fixtures were recorded from GeoServer 2.27.1 (docker.osgeo.org/geoserver)
against the sample ``topp:tasmania_roads`` layer.
"""

import datetime as dt
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from deckgl_marimo.wfs import FeatureTypeInfo, WFSError, build_transaction_xml, parse_transaction_response

FIX = Path(__file__).parent / "fixtures"

ROADS = FeatureTypeInfo(
    typename="topp:tasmania_roads", prefix="topp", local_name="tasmania_roads",
    namespace="http://www.openplans.org/topp", geometry_name="the_geom",
    geometry_type="MultiLineString", properties={"TYPE": "xsd:string"},
)
LINE = {"type": "LineString", "coordinates": [[146.0, -42.0], [146.5, -42.2]]}
FEATURE = {"type": "Feature", "geometry": LINE, "properties": {"TYPE": "dgl", "shape": "Rectangle", "editProperties": {}}}


def _xml(b: bytes) -> ET.Element:
    return ET.fromstring(b)


def _strip_ids(s: str) -> str:
    return re.sub(r' gml:id="[^"]+"', "", s)


class TestBuild200:
    def test_insert(self):
        body = build_transaction_xml(ROADS, inserts=[FEATURE])
        text = _strip_ids(body.decode())
        assert text.startswith('<?xml version="1.0" encoding="UTF-8"?><wfs:Transaction service="WFS" version="2.0.0" ')
        assert 'xmlns:wfs="http://www.opengis.net/wfs/2.0"' in text
        assert 'xmlns:fes="http://www.opengis.net/fes/2.0"' in text
        assert 'xmlns:gml="http://www.opengis.net/gml/3.2"' in text
        assert 'xmlns:topp="http://www.openplans.org/topp"' in text
        assert (
            "<wfs:Insert><topp:tasmania_roads><topp:the_geom>"
            '<gml:MultiCurve srsName="urn:ogc:def:crs:EPSG::4326"><gml:curveMember><gml:LineString>'
            "<gml:posList>-42 146 -42.2 146.5</gml:posList>"
        ) in text  # promoted to Multi*, lat/lon swapped
        assert "<topp:TYPE>dgl</topp:TYPE>" in text
        assert "shape" not in text and "editProperties" not in text  # non-schema props dropped
        _xml(body)  # well-formed

    def test_update_geometry_and_property(self):
        body = build_transaction_xml(ROADS, updates=[("tasmania_roads.1", {"geometry": LINE, "properties": {"TYPE": "x<y"}})])
        text = _strip_ids(body.decode())
        assert '<wfs:Update typeName="topp:tasmania_roads">' in text
        assert "<wfs:Property><wfs:ValueReference>the_geom</wfs:ValueReference><wfs:Value><gml:MultiCurve" in text
        assert "<wfs:Property><wfs:ValueReference>TYPE</wfs:ValueReference><wfs:Value>x&lt;y</wfs:Value></wfs:Property>" in text
        assert '<fes:Filter><fes:ResourceId rid="tasmania_roads.1"/></fes:Filter></wfs:Update>' in text
        _xml(body)

    def test_update_null_property_sends_empty_value(self):
        body = build_transaction_xml(ROADS, updates=[("r.1", {"geometry": None, "properties": {"TYPE": None}})])
        assert "<wfs:Value></wfs:Value>" in body.decode()

    def test_update_with_nothing_applicable_raises(self):
        with pytest.raises(WFSError, match="nothing to apply"):
            build_transaction_xml(ROADS, updates=[("r.1", {"geometry": None, "properties": {"NOPE": 1}})])

    def test_delete(self):
        body = build_transaction_xml(ROADS, deletes=["tasmania_roads.3", 'a"b'])
        text = body.decode()
        assert '<wfs:Delete typeName="topp:tasmania_roads"><fes:Filter><fes:ResourceId rid="tasmania_roads.3"/></fes:Filter></wfs:Delete>' in text
        assert "rid='a\"b'" in text
        _xml(body)

    def test_order_insert_update_delete(self):
        body = build_transaction_xml(ROADS, inserts=[FEATURE], updates=[("r.1", {"properties": {"TYPE": "a"}})], deletes=["r.2"]).decode()
        assert body.index("<wfs:Insert>") < body.index("<wfs:Update") < body.index("<wfs:Delete")

    def test_value_formatting(self):
        info = FeatureTypeInfo("ns:t", "ns", "t", "urn:x", None, None, {"flag": "xsd:boolean", "when": "xsd:date", "n": "xsd:int"})
        body = build_transaction_xml(info, inserts=[{"geometry": None, "properties": {"flag": True, "when": dt.date(2026, 8, 22), "n": 3}}]).decode()
        assert "<ns:flag>true</ns:flag><ns:when>2026-08-22</ns:when><ns:n>3</ns:n>" in body

    def test_geometry_into_geometryless_type_raises(self):
        info = FeatureTypeInfo("ns:t", "ns", "t", "urn:x", None, None, {"a": "xsd:string"})
        with pytest.raises(WFSError, match="no geometry property"):
            build_transaction_xml(info, inserts=[FEATURE])


class TestBuildLegacy:
    def test_110_uses_ogc_filter_and_name(self):
        body = build_transaction_xml(
            ROADS, version="1.1.0", updates=[("r.1", {"properties": {"TYPE": "a"}})], deletes=["r.2"],
        ).decode()
        assert 'version="1.1.0"' in body
        assert 'xmlns:wfs="http://www.opengis.net/wfs"' in body and 'xmlns:ogc="http://www.opengis.net/ogc"' in body
        assert "<wfs:Property><wfs:Name>TYPE</wfs:Name><wfs:Value>a</wfs:Value></wfs:Property>" in body
        assert '<ogc:Filter><ogc:FeatureId fid="r.1"/></ogc:Filter>' in body
        assert '<wfs:Delete typeName="topp:tasmania_roads"><ogc:Filter><ogc:FeatureId fid="r.2"/></ogc:Filter></wfs:Delete>' in body
        assert "gml:id" not in body

    def test_100_uses_gml2(self):
        body = build_transaction_xml(ROADS, version="1.0.0", inserts=[FEATURE], srs_name="EPSG:4326", swap_axes=False).decode()
        assert '<gml:MultiLineString srsName="EPSG:4326"><gml:lineStringMember><gml:LineString><gml:coordinates>146,-42 146.5,-42.2' in body

    def test_unknown_version(self):
        with pytest.raises(ValueError):
            build_transaction_xml(ROADS, version="3.0.0")


class TestParseResponse:
    @pytest.mark.parametrize("version, vtag", [("2.0.0", "200"), ("1.1.0", "110")])
    def test_insert_update_delete_summaries(self, version, vtag):
        ins = parse_transaction_response((FIX / f"txresponse_insert_{vtag}.xml").read_bytes(), version=version)
        assert (ins.inserted, ins.updated, ins.deleted) == (1, 0, 0)
        assert ins.inserted_ids == ["new0"]  # GeoServer shapefile placeholder id
        assert ins.total == 1
        upd = parse_transaction_response((FIX / f"txresponse_update_{vtag}.xml").read_bytes(), version=version)
        assert (upd.inserted, upd.updated, upd.deleted) == (0, 1, 0)
        assert upd.inserted_ids == []  # fid="none" must not leak through
        dele = parse_transaction_response((FIX / f"txresponse_delete_{vtag}.xml").read_bytes(), version=version)
        assert (dele.inserted, dele.updated, dele.deleted) == (0, 0, 1)
        assert "TransactionResponse" in dele.raw

    def test_100_success(self):
        ins = parse_transaction_response((FIX / "txresponse_insert_100.xml").read_bytes(), version="1.0.0")
        assert ins.inserted == 1 and ins.inserted_ids == ["new0"]
        upd = parse_transaction_response((FIX / "txresponse_update_100.xml").read_bytes(), version="1.0.0")
        assert upd.inserted == 0 and upd.inserted_ids == []

    def test_100_failed_raises(self):
        body = (
            b'<wfs:WFS_TransactionResponse xmlns:wfs="http://www.opengis.net/wfs" xmlns:ogc="http://www.opengis.net/ogc">'
            b"<wfs:TransactionResult><wfs:Status><wfs:FAILED/></wfs:Status><wfs:Message>boom</wfs:Message>"
            b"</wfs:TransactionResult></wfs:WFS_TransactionResponse>"
        )
        with pytest.raises(WFSError, match="FAILED: boom") as ei:
            parse_transaction_response(body, version="1.0.0")
        assert ei.value.code == "FAILED"

    def test_real_ids_when_store_reports_them(self):
        body = (
            b'<wfs:TransactionResponse xmlns:wfs="http://www.opengis.net/wfs/2.0" xmlns:fes="http://www.opengis.net/fes/2.0">'
            b"<wfs:TransactionSummary><wfs:totalInserted>2</wfs:totalInserted><wfs:totalUpdated>0</wfs:totalUpdated>"
            b"<wfs:totalDeleted>0</wfs:totalDeleted></wfs:TransactionSummary><wfs:InsertResults>"
            b'<wfs:Feature><fes:ResourceId rid="roads.15"/></wfs:Feature><wfs:Feature><fes:ResourceId rid="roads.16"/></wfs:Feature>'
            b"</wfs:InsertResults></wfs:TransactionResponse>"
        )
        assert parse_transaction_response(body).inserted_ids == ["roads.15", "roads.16"]

    def test_ows_exception_raises(self):
        with pytest.raises(WFSError, match=r"InvalidParameterValue") as ei:
            parse_transaction_response((FIX / "exception_ows_200.xml").read_bytes(), status=400)
        assert ei.value.code == "InvalidParameterValue"
        assert ei.value.status == 400
        assert ei.value.locator

    def test_service_exception_raises(self):
        with pytest.raises(WFSError) as ei:
            parse_transaction_response((FIX / "exception_se_100.xml").read_bytes(), version="1.0.0")
        assert ei.value.code

    def test_non_xml_raises(self):
        with pytest.raises(WFSError, match="non-XML"):
            parse_transaction_response(b"<html>nope", status=500)
        with pytest.raises(WFSError, match="non-XML"):
            parse_transaction_response(b'{"type": "FeatureCollection"}')

    def test_unrecognised_xml_raises(self):
        with pytest.raises(WFSError, match="Unrecognised"):
            parse_transaction_response(b"<foo/>")
