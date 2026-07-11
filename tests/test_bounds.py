"""Tests for compute_bounds and Map.fit_bounds (#21)."""

import pytest

from deckgl_marimo import Map, compute_bounds


class TestComputeBounds:
    def test_point_pairs(self):
        pts = [[-122.4, 37.8], [-122.3, 37.9], [-122.5, 37.7]]
        assert compute_bounds(pts) == [[-122.5, 37.7], [-122.3, 37.9]]

    def test_dicts_with_position_key(self):
        data = [{"position": [-10, -5]}, {"position": [10, 5]}]
        assert compute_bounds(data) == [[-10, -5], [10, 5]]

    def test_dicts_with_path_key(self):
        data = [{"path": [[0, 0], [1, 2]]}, {"path": [[-3, 4], [5, -6]]}]
        assert compute_bounds(data) == [[-3, -6], [5, 4]]

    def test_geojson_feature_collection(self):
        fc = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [100.0, 0.5]},
                    "properties": {},
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[101.0, 1.0], [102.0, 2.0], [101.5, 0.0], [101.0, 1.0]]],
                    },
                    "properties": {},
                },
            ],
        }
        assert compute_bounds(fc) == [[100.0, 0.0], [102.0, 2.0]]

    def test_position_columns_from_rows(self):
        data = [{"lon": -1.0, "lat": 2.0}, {"lon": 3.0, "lat": -4.0}]
        assert compute_bounds(data, position=["lon", "lat"]) == [[-1.0, -4.0], [3.0, 2.0]]

    def test_position_columns_from_dataframe(self):
        pd = pytest.importorskip("pandas")
        df = pd.DataFrame({"lon": [-1.0, 3.0], "lat": [2.0, -4.0]})
        assert compute_bounds(df, position=["lon", "lat"]) == [[-1.0, -4.0], [3.0, 2.0]]

    def test_get_coordinates_accessor(self):
        data = [{"where": [7, 8]}, {"where": [9, 10]}]
        bounds = compute_bounds(data, get_coordinates=lambda row: row["where"])
        assert bounds == [[7, 8], [9, 10]]

    def test_no_coordinates_raises(self):
        with pytest.raises(ValueError, match="no coordinates"):
            compute_bounds([{"name": "x"}])

    def test_source_target_positions(self):
        data = [{"source_position": [0, 0], "target_position": [10, 10]}]
        assert compute_bounds(data) == [[0, 0], [10, 10]]


class TestFitBounds:
    def test_sets_center_zoom_and_request(self):
        m = Map()
        m.fit_bounds([[-10.0, -5.0], [10.0, 5.0]], padding=40)
        assert m.longitude == 0.0
        assert m.latitude == 0.0
        assert m.zoom > 0
        req = m.fit_bounds_request
        assert req["bounds"] == [[-10.0, -5.0], [10.0, 5.0]]
        assert req["padding"] == 40
        assert req["_seq"] == 1

    def test_repeated_identical_bounds_still_fire(self):
        m = Map()
        m.fit_bounds([[0, 0], [1, 1]])
        first = m.fit_bounds_request["_seq"]
        m.fit_bounds([[0, 0], [1, 1]])
        assert m.fit_bounds_request["_seq"] == first + 1

    def test_smaller_bounds_zoom_in_more(self):
        m1, m2 = Map(), Map()
        m1.fit_bounds([[-40, -20], [40, 20]])
        m2.fit_bounds([[-1, -0.5], [1, 0.5]])
        assert m2.zoom > m1.zoom
