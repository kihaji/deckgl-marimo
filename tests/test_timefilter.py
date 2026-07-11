"""Tests for the time-filter helpers and DataFilterExtension wiring (#36)."""

import pytest

from deckgl_marimo import Map, ScatterplotLayer, build_time_filter, compute_time_domain


class TestComputeTimeDomain:
    def test_list_of_dicts(self):
        data = [{"t": 3}, {"t": 1}, {"t": 7}]
        assert compute_time_domain(data, "t") == [1.0, 7.0]

    def test_dotted_path_over_geojson(self):
        fc = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "properties": {"t": 5}, "geometry": None},
                {"type": "Feature", "properties": {"t": 2}, "geometry": None},
            ],
        }
        assert compute_time_domain(fc, "properties.t") == [2.0, 5.0]

    def test_callable_accessor(self):
        data = [{"a": 1, "b": 2}, {"a": 4, "b": 1}]
        assert compute_time_domain(data, lambda row: row["a"] + row["b"]) == [3.0, 5.0]

    def test_dataframe(self):
        pd = pytest.importorskip("pandas")
        df = pd.DataFrame({"t": [10.0, 4.0, 8.0]})
        assert compute_time_domain(df, "t") == [4.0, 10.0]

    def test_skips_non_numeric_and_bools(self):
        data = [{"t": None}, {"t": "x"}, {"t": True}, {"t": 2}]
        assert compute_time_domain(data, "t") == [2.0, 2.0]

    def test_no_values_raises(self):
        with pytest.raises(ValueError, match="no numeric time values"):
            compute_time_domain([{"t": None}], "t")


class TestBuildTimeFilter:
    def test_defaults(self):
        tf = build_time_filter([0.0, 100.0], window=10)
        assert tf["domain"] == [0.0, 100.0]
        assert tf["window"] == 10
        assert tf["current"] == 10.0          # first full window
        assert tf["playing"] is False
        assert tf["speed"] == 5.0             # full sweep in ~20s
        assert tf["loop"] is True
        assert "softEdge" not in tf
        assert "layerIds" not in tf

    def test_explicit_options(self):
        tf = build_time_filter(
            [0, 10], window=2, current=5, playing=True, speed=1.5,
            loop=False, soft_edge=0.5, layer_ids=["a"], nonce=3,
        )
        assert tf["current"] == 5
        assert tf["playing"] is True
        assert tf["softEdge"] == 0.5
        assert tf["layerIds"] == ["a"]
        assert tf["nonce"] == 3


class TestFilterProps:
    def test_auto_attaches_extension(self):
        layer = ScatterplotLayer(
            data=[{"lon": 0, "lat": 0, "t": 1}],
            get_position=["lon", "lat"],
            get_filter_value="t",
        )
        spec = layer.to_spec()
        assert spec["getFilterValue"] == "t"
        assert spec["extensions"] == ["DataFilterExtension"]

    def test_explicit_extensions_win(self):
        layer = ScatterplotLayer(get_filter_value="t", extensions=["DataFilterExtension"])
        assert layer.to_spec()["extensions"] == ["DataFilterExtension"]

    def test_filter_range_reactive_alternative(self):
        layer = ScatterplotLayer(get_filter_value="t", filter_range=[0, 5])
        spec = layer.to_spec()
        assert spec["filterRange"] == [0, 5]

    def test_no_extension_without_filter_value(self):
        assert "extensions" not in ScatterplotLayer().to_spec()


class TestMapTimeFilter:
    def test_constructor_and_traitlets(self):
        tf = build_time_filter([0, 10], window=2)
        m = Map(time_filter=tf)
        assert m.time_filter["window"] == 2
        assert m.current_time == 0.0

    def test_runtime_update(self):
        m = Map()
        assert m.time_filter == {}
        m.time_filter = build_time_filter([0, 10], window=2, playing=True)
        assert m.time_filter["playing"] is True
