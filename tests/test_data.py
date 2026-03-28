"""Tests for data conversion utilities."""

from deckgl_marimo._data import (
    dataframe_to_positions,
    dataframe_to_records,
    prepare_data,
)


class TestDataframeToPositions:
    def test_list_of_dicts(self):
        data = [{"lat": 51.5, "lon": -0.1}, {"lat": 52.2, "lon": -1.4}]
        result = dataframe_to_positions(data)
        assert result == [[-0.1, 51.5], [-1.4, 52.2]]

    def test_custom_column_names(self):
        data = [{"latitude": 10.0, "longitude": 20.0}]
        result = dataframe_to_positions(data, lat_col="latitude", lon_col="longitude")
        assert result == [[20.0, 10.0]]

    def test_empty_list(self):
        assert dataframe_to_positions([]) == []

    def test_pandas_dataframe(self):
        pd = __import__("pandas")
        df = pd.DataFrame({"lat": [1.0, 2.0], "lon": [3.0, 4.0]})
        result = dataframe_to_positions(df)
        assert result == [[3.0, 1.0], [4.0, 2.0]]

    def test_polars_dataframe(self):
        pl = __import__("polars")
        df = pl.DataFrame({"lat": [1.0, 2.0], "lon": [3.0, 4.0]})
        result = dataframe_to_positions(df)
        assert result == [[3.0, 1.0], [4.0, 2.0]]


class TestDataframeToRecords:
    def test_pandas(self):
        pd = __import__("pandas")
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        result = dataframe_to_records(df)
        assert result == [{"a": 1, "b": 3}, {"a": 2, "b": 4}]

    def test_polars(self):
        pl = __import__("polars")
        df = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
        result = dataframe_to_records(df)
        assert result == [{"a": 1, "b": 3}, {"a": 2, "b": 4}]


class TestPrepareData:
    def test_none(self):
        assert prepare_data(None) == []

    def test_string_passthrough(self):
        assert prepare_data("https://example.com/data.json") == "https://example.com/data.json"

    def test_dict_passthrough(self):
        geojson = {"type": "FeatureCollection", "features": []}
        assert prepare_data(geojson) == geojson

    def test_list_passthrough(self):
        data = [{"x": 1}, {"x": 2}]
        assert prepare_data(data) == data

    def test_pandas_dataframe(self):
        pd = __import__("pandas")
        df = pd.DataFrame({"lon": [1.0], "lat": [2.0]})
        result = prepare_data(df)
        assert result == [{"lon": 1.0, "lat": 2.0}]

    def test_unsupported_type(self):
        import pytest

        with pytest.raises(TypeError, match="Unsupported data type"):
            prepare_data(42)

    def test_duckdb_relation(self):
        duckdb = __import__("duckdb")
        rel = duckdb.sql("SELECT 1 AS x, 2 AS y")
        result = prepare_data(rel)
        assert result == [{"x": 1, "y": 2}]
