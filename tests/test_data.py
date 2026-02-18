from deckgl_marimo._data import dataframe_to_positions


def test_list_of_dicts():
    data = [{"lat": 51.5, "lon": -0.1}, {"lat": 52.2, "lon": -1.4}]
    result = dataframe_to_positions(data)
    assert result == [[-0.1, 51.5], [-1.4, 52.2]]


def test_custom_column_names():
    data = [{"latitude": 10.0, "longitude": 20.0}]
    result = dataframe_to_positions(data, lat_col="latitude", lon_col="longitude")
    assert result == [[20.0, 10.0]]


def test_empty_list():
    assert dataframe_to_positions([]) == []


def test_pandas_dataframe():
    pd = __import__("pandas")
    df = pd.DataFrame({"lat": [1.0, 2.0], "lon": [3.0, 4.0]})
    result = dataframe_to_positions(df)
    assert result == [[3.0, 1.0], [4.0, 2.0]]


def test_polars_dataframe():
    pl = __import__("polars")
    df = pl.DataFrame({"lat": [1.0, 2.0], "lon": [3.0, 4.0]})
    result = dataframe_to_positions(df)
    assert result == [[3.0, 1.0], [4.0, 2.0]]
