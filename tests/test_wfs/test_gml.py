"""Tests for the GeoJSON -> GML encoder."""

import re

import pytest

from deckgl_marimo.wfs import WFSError, geometry_to_gml
from deckgl_marimo.wfs._gml import normalize_gml_type, promote_geometry

POINT = {"type": "Point", "coordinates": [-146.46, -41.24]}
LINE = {"type": "LineString", "coordinates": [[-146.46, -41.24], [146.57, -41.25]]}
POLY = {
    "type": "Polygon",
    "coordinates": [
        [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]],
        [[2, 2], [3, 2], [3, 3], [2, 2]],
    ],
}
MPOINT = {"type": "MultiPoint", "coordinates": [[1, 2], [3, 4]]}
MLINE = {"type": "MultiLineString", "coordinates": [[[1, 2], [3, 4]], [[5, 6], [7, 8]]]}
MPOLY = {"type": "MultiPolygon", "coordinates": [[[[0, 0], [1, 0], [1, 1], [0, 0]]]]}
GC = {"type": "GeometryCollection", "geometries": [POINT, LINE]}


def _strip_ids(xml: str) -> str:
    return re.sub(r' gml:id="[^"]+"', "", xml)


class TestGml32:
    def test_point_lat_lon_swapped_with_urn(self):
        xml = geometry_to_gml(POINT)
        assert _strip_ids(xml) == (
            '<gml:Point srsName="urn:ogc:def:crs:EPSG::4326"><gml:pos>-41.24 -146.46</gml:pos></gml:Point>'
        )
        assert re.search(r'<gml:Point gml:id="g[0-9a-f]{8}\.1"', xml)

    def test_no_swap_when_requested(self):
        xml = geometry_to_gml(POINT, srs_name="EPSG:4326", swap_axes=False)
        assert "<gml:pos>-146.46 -41.24</gml:pos>" in xml
        assert 'srsName="EPSG:4326"' in xml

    def test_linestring_poslist(self):
        xml = _strip_ids(geometry_to_gml(LINE, swap_axes=False))
        assert xml == (
            '<gml:LineString srsName="urn:ogc:def:crs:EPSG::4326">'
            "<gml:posList>-146.46 -41.24 146.57 -41.25</gml:posList></gml:LineString>"
        )

    def test_polygon_exterior_interior(self):
        xml = _strip_ids(geometry_to_gml(POLY, swap_axes=False))
        assert xml.startswith('<gml:Polygon srsName="urn:ogc:def:crs:EPSG::4326"><gml:exterior><gml:LinearRing>')
        assert "<gml:posList>0 0 10 0 10 10 0 10 0 0</gml:posList>" in xml
        assert "<gml:interior><gml:LinearRing><gml:posList>2 2 3 2 3 3 2 2</gml:posList>" in xml
        assert xml.endswith("</gml:interior></gml:Polygon>")

    def test_multis_use_gml3_containers(self):
        assert "<gml:MultiPoint" in geometry_to_gml(MPOINT)
        assert "<gml:pointMember><gml:Point" in _strip_ids(geometry_to_gml(MPOINT))
        mline = _strip_ids(geometry_to_gml(MLINE))
        assert mline.startswith("<gml:MultiCurve srsName=")
        assert "<gml:curveMember><gml:LineString>" in mline
        mpoly = _strip_ids(geometry_to_gml(MPOLY))
        assert mpoly.startswith("<gml:MultiSurface srsName=")
        assert "<gml:surfaceMember><gml:Polygon>" in mpoly

    def test_every_geometry_element_gets_a_gml_id(self):
        xml = geometry_to_gml(MPOLY)
        # MultiSurface + Polygon + LinearRing
        assert len(re.findall(r'gml:id="', xml)) == 3
        assert xml.count("srsName=") == 1  # only on the outer element

    def test_geometry_collection(self):
        xml = _strip_ids(geometry_to_gml(GC, swap_axes=False))
        assert xml.startswith("<gml:MultiGeometry srsName=")
        assert xml.count("<gml:geometryMember>") == 2

    def test_extra_dimensions_dropped(self):
        xml = geometry_to_gml({"type": "Point", "coordinates": [1.5, 2.5, 99]}, swap_axes=False)
        assert "<gml:pos>1.5 2.5</gml:pos>" in xml

    def test_number_formatting(self):
        xml = geometry_to_gml({"type": "Point", "coordinates": [1, -0.0000001]}, swap_axes=False)
        assert "<gml:pos>1 -0.0000001</gml:pos>" in xml


class TestGml311:
    def test_no_gml_ids_and_poslist(self):
        xml = geometry_to_gml(LINE, version="1.1.0", swap_axes=False)
        assert "gml:id" not in xml
        assert "<gml:posList>" in xml


class TestGml2:
    def test_point_coordinates(self):
        xml = geometry_to_gml(POINT, version="1.0.0", srs_name="EPSG:4326", swap_axes=False)
        assert xml == '<gml:Point srsName="EPSG:4326"><gml:coordinates>-146.46,-41.24</gml:coordinates></gml:Point>'

    def test_polygon_boundaries(self):
        xml = geometry_to_gml(POLY, version="1.0.0", srs_name="EPSG:4326", swap_axes=False)
        assert "<gml:outerBoundaryIs><gml:LinearRing><gml:coordinates>0,0 10,0 10,10 0,10 0,0</gml:coordinates>" in xml
        assert "<gml:innerBoundaryIs>" in xml

    def test_multis_use_gml2_containers(self):
        xml = geometry_to_gml(MLINE, version="1.0.0", srs_name="EPSG:4326", swap_axes=False)
        assert xml.startswith('<gml:MultiLineString srsName="EPSG:4326"><gml:lineStringMember><gml:LineString>')
        assert "<gml:MultiPolygon" in geometry_to_gml(MPOLY, version="1.0.0", swap_axes=False)


class TestPromotion:
    def test_single_promoted_to_multi(self):
        assert promote_geometry(LINE, "MultiLineString") == {"type": "MultiLineString", "coordinates": [LINE["coordinates"]]}
        assert promote_geometry(POLY, "MultiPolygon")["type"] == "MultiPolygon"
        assert promote_geometry(POINT, "MultiPoint")["type"] == "MultiPoint"

    def test_unconstrained_and_matching_pass_through(self):
        assert promote_geometry(POINT, None) is POINT
        assert promote_geometry(POINT, "Geometry") is POINT
        assert promote_geometry(MPOLY, "MultiPolygon") is MPOLY

    def test_mismatch_raises(self):
        with pytest.raises(WFSError, match="does not match"):
            promote_geometry(POINT, "MultiPolygon")

    def test_encoder_applies_target_type(self):
        xml = geometry_to_gml(LINE, target_type="MultiLineString")
        assert xml.startswith("<gml:MultiCurve")

    def test_normalize_gml_type(self):
        assert normalize_gml_type("gml:MultiSurfacePropertyType") == "MultiPolygon"
        assert normalize_gml_type("MultiCurvePropertyType") == "MultiLineString"
        assert normalize_gml_type("gml:PointPropertyType") == "Point"
        assert normalize_gml_type("gml:GeometryPropertyType") == "Geometry"
        assert normalize_gml_type("gml:MultiLineStringPropertyType") == "MultiLineString"

    def test_unknown_type_raises(self):
        with pytest.raises(WFSError, match="Unsupported"):
            geometry_to_gml({"type": "Circle", "coordinates": [0, 0]})
