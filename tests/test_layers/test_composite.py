"""Tests for composite layers."""

import math

import pytest

from deckgl_marimo.layers._composite import (
    DisplacementLayer,
    EllipseLayer,
    _compute_ellipse_ring,
)
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

    def test_zoom_bounds_propagate(self):
        specs = self._make(min_zoom=8, max_zoom=14).to_specs()
        assert len(specs) == 3
        for spec in specs:
            assert spec["minZoom"] == 8
            assert spec["maxZoom"] == 14


# =====================================================================
# _compute_ellipse_ring
# =====================================================================

ELLIPSE_DATA = [
    {"lon": -122.4, "lat": 37.8, "major": 1000, "minor": 500, "angle": 45},
    {"lon": -122.5, "lat": 37.9, "major": 2000, "minor": 1000, "angle": 90},
]


class TestComputeEllipseRing:
    def test_ring_is_closed(self):
        ring = _compute_ellipse_ring(0.0, 0.0, 1000, 500, 0.0, 32)
        assert ring[0] == ring[-1]

    def test_vertex_count(self):
        ring = _compute_ellipse_ring(0.0, 0.0, 1000, 500, 0.0, 64)
        assert len(ring) == 65  # num_vertices + 1 (closing point)

    def test_vertex_count_small(self):
        ring = _compute_ellipse_ring(0.0, 0.0, 1000, 500, 0.0, 8)
        assert len(ring) == 9

    def test_circle_equidistant(self):
        """For a circle (equal axes), all points should be roughly equidistant from center."""
        ring = _compute_ellipse_ring(0.0, 0.0, 500, 500, 0.0, 32)
        distances = []
        for lon, lat in ring[:-1]:
            # Approximate distance at equator
            d = math.sqrt(
                (lon * 111_320) ** 2 + (lat * 111_320) ** 2
            )
            distances.append(d)
        avg = sum(distances) / len(distances)
        for d in distances:
            assert abs(d - avg) / avg < 0.01  # within 1%

    def test_center_location(self):
        """Ring should be centered around the given center."""
        ring = _compute_ellipse_ring(10.0, 20.0, 100, 100, 0.0, 16)
        avg_lon = sum(p[0] for p in ring[:-1]) / 16
        avg_lat = sum(p[1] for p in ring[:-1]) / 16
        assert abs(avg_lon - 10.0) < 1e-6
        assert abs(avg_lat - 20.0) < 1e-6

    def test_orientation_zero_major_north(self):
        """At orientation=0, major axis should extend along latitude (north-south)."""
        ring = _compute_ellipse_ring(0.0, 0.0, 1000, 100, 0.0, 4)
        # With 4 vertices, we get points at 0, 90, 180, 270 degrees of the parametric angle
        # At theta=pi/2 (i=1): x=0, y=semi_major → should be the northernmost point
        lats = [p[1] for p in ring[:-1]]
        max_lat_idx = lats.index(max(lats))
        assert max_lat_idx == 1  # second vertex should be northernmost


# =====================================================================
# EllipseLayer
# =====================================================================


class TestEllipseLayer:
    def _make(self, **kwargs):
        defaults = dict(
            data=ELLIPSE_DATA,
            center=["lon", "lat"],
            major_axis="major",
            minor_axis="minor",
            orientation="angle",
        )
        defaults.update(kwargs)
        return EllipseLayer(**defaults)

    def test_produces_one_spec_by_default(self):
        """Default has polygon only (center dots off by default)."""
        specs = self._make().to_specs()
        assert len(specs) == 1
        assert specs[0]["type"] == "PolygonLayer"

    def test_spec_types_with_center_dots(self):
        specs = self._make(show_center_dots=True).to_specs()
        assert len(specs) == 2
        assert specs[0]["type"] == "PolygonLayer"
        assert specs[1]["type"] == "ScatterplotLayer"

    def test_sub_layer_ids(self):
        layer = self._make(id="test", show_center_dots=True)
        specs = layer.to_specs()
        assert specs[0]["id"] == "test-rings"
        assert specs[1]["id"] == "test-centers"

    def test_polygon_column_added(self):
        specs = self._make().to_specs()
        poly_data = specs[0]["data"]
        for row in poly_data:
            assert "_ellipse_polygon" in row

    def test_ring_is_closed(self):
        specs = self._make().to_specs()
        ring = specs[0]["data"][0]["_ellipse_polygon"]
        assert ring[0] == ring[-1]

    def test_ring_vertex_count(self):
        specs = self._make(num_vertices=32).to_specs()
        ring = specs[0]["data"][0]["_ellipse_polygon"]
        assert len(ring) == 33

    def test_constant_major_axis(self):
        layer = EllipseLayer(
            data=[{"lon": 0, "lat": 0}],
            center=["lon", "lat"],
            major_axis=1000.0,
        )
        specs = layer.to_specs()
        assert "_ellipse_polygon" in specs[0]["data"][0]

    def test_minor_defaults_to_major(self):
        """When minor_axis is None, produces a circle."""
        layer = EllipseLayer(
            data=[{"lon": 0, "lat": 0}],
            center=["lon", "lat"],
            major_axis=1000.0,
        )
        specs = layer.to_specs()
        ring = specs[0]["data"][0]["_ellipse_polygon"]
        # Check roughly circular: max lat offset ≈ max lon offset
        lats = [p[1] for p in ring[:-1]]
        lons = [p[0] for p in ring[:-1]]
        lat_range = max(lats) - min(lats)
        lon_range = max(lons) - min(lons)
        assert abs(lat_range - lon_range) / lat_range < 0.01

    def test_is_semi_mode(self):
        """is_semi=True should produce ellipses twice the size of is_semi=False with same values."""
        specs_diameter = self._make(
            data=[{"lon": 0, "lat": 0, "major": 1000, "minor": 500, "angle": 0}],
            is_semi=False,
        ).to_specs()
        specs_semi = self._make(
            data=[{"lon": 0, "lat": 0, "major": 1000, "minor": 500, "angle": 0}],
            is_semi=True,
        ).to_specs()
        ring_d = specs_diameter[0]["data"][0]["_ellipse_polygon"]
        ring_s = specs_semi[0]["data"][0]["_ellipse_polygon"]
        # Semi mode should be bigger (2x)
        lat_range_d = max(p[1] for p in ring_d) - min(p[1] for p in ring_d)
        lat_range_s = max(p[1] for p in ring_s) - min(p[1] for p in ring_s)
        assert abs(lat_range_s / lat_range_d - 2.0) < 0.01

    def test_radians_mode(self):
        """orientation_units='radians' should use values directly."""
        specs_deg = self._make(
            data=[{"lon": 0, "lat": 0, "major": 1000, "minor": 500, "angle": 90}],
            orientation_units="degrees",
        ).to_specs()
        specs_rad = self._make(
            data=[{"lon": 0, "lat": 0, "major": 1000, "minor": 500, "angle": math.radians(90)}],
            orientation_units="radians",
        ).to_specs()
        ring_deg = specs_deg[0]["data"][0]["_ellipse_polygon"]
        ring_rad = specs_rad[0]["data"][0]["_ellipse_polygon"]
        for p1, p2 in zip(ring_deg, ring_rad, strict=True):
            assert abs(p1[0] - p2[0]) < 1e-10
            assert abs(p1[1] - p2[1]) < 1e-10

    def test_kilometers_unit(self):
        """1 km should produce same result as 1000 meters."""
        specs_m = self._make(
            data=[{"lon": 0, "lat": 0, "major": 1000, "minor": 500, "angle": 0}],
            units="meters",
        ).to_specs()
        specs_km = self._make(
            data=[{"lon": 0, "lat": 0, "major": 1, "minor": 0.5, "angle": 0}],
            units="kilometers",
        ).to_specs()
        ring_m = specs_m[0]["data"][0]["_ellipse_polygon"]
        ring_km = specs_km[0]["data"][0]["_ellipse_polygon"]
        for p1, p2 in zip(ring_m, ring_km, strict=True):
            assert abs(p1[0] - p2[0]) < 1e-10
            assert abs(p1[1] - p2[1]) < 1e-10

    def test_nautical_miles_unit(self):
        """1 NM should produce same result as 1852 meters."""
        specs_m = self._make(
            data=[{"lon": 0, "lat": 0, "major": 1852, "minor": 926, "angle": 0}],
            units="meters",
        ).to_specs()
        specs_nm = self._make(
            data=[{"lon": 0, "lat": 0, "major": 1, "minor": 0.5, "angle": 0}],
            units="nautical_miles",
        ).to_specs()
        ring_m = specs_m[0]["data"][0]["_ellipse_polygon"]
        ring_nm = specs_nm[0]["data"][0]["_ellipse_polygon"]
        for p1, p2 in zip(ring_m, ring_nm, strict=True):
            assert abs(p1[0] - p2[0]) < 1e-10
            assert abs(p1[1] - p2[1]) < 1e-10

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
            assert len(spec["data"]) == len(ELLIPSE_DATA)

    def test_fill_color_default(self):
        specs = self._make().to_specs()
        assert specs[0]["getFillColor"] == [0, 140, 255, 100]

    def test_custom_fill_color(self):
        specs = self._make(fill_color=[255, 0, 0, 200]).to_specs()
        assert specs[0]["getFillColor"] == [255, 0, 0, 200]

    def test_to_spec_returns_polygon(self):
        spec = self._make().to_spec()
        assert spec["type"] == "PolygonLayer"

    def test_invalid_orientation_units(self):
        with pytest.raises(ValueError, match="orientation_units"):
            self._make(orientation_units="grads")

    def test_invalid_units(self):
        with pytest.raises(ValueError, match="units"):
            self._make(units="feet")

    def test_invalid_num_vertices(self):
        with pytest.raises(ValueError, match="num_vertices"):
            self._make(num_vertices=2)

    def test_zoom_bounds_propagate(self):
        specs = self._make(show_center_dots=True, min_zoom=8, max_zoom=14).to_specs()
        assert len(specs) == 2
        for spec in specs:
            assert spec["minZoom"] == 8
            assert spec["maxZoom"] == 14
