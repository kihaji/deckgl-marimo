"""Data conversion utilities for deckgl-marimo.

Supports pandas, polars (via narwhals), geopandas, DuckDB relations,
plain dicts, and GeoJSON.
"""

from __future__ import annotations

from typing import Any

import narwhals.stable.v2 as nw


def prepare_data(data: Any) -> list | dict | str:
    """Universal data preparation for deck.gl layers.

    Detects the input type and converts to a JSON-serializable format
    suitable for deck.gl consumption.

    Parameters
    ----------
    data
        One of:
        - pandas/polars DataFrame -> list of dicts
        - GeoDataFrame (has __geo_interface__) -> GeoJSON FeatureCollection
        - DuckDB Relation (has .fetchdf()) -> converted via fetchdf() then recursed
        - list[dict] -> passed through
        - dict -> passed through (assumed GeoJSON)
        - str -> passed through (assumed URL or file path)

    Returns
    -------
    list | dict | str
        JSON-serializable data for deck.gl.
    """
    if data is None:
        return []

    # String: URL or file path — pass through for JS to handle
    if isinstance(data, str):
        return data

    # Dict: assumed GeoJSON — pass through
    if isinstance(data, dict):
        return data

    # List: assumed list of dicts — pass through
    if isinstance(data, list):
        return data

    # DuckDB Relation: has .fetchdf() method
    if hasattr(data, "fetchdf"):
        return prepare_data(data.fetchdf())

    # GeoDataFrame: has __geo_interface__
    if hasattr(data, "__geo_interface__"):
        return geodataframe_to_geojson(data)

    # pandas/polars DataFrame via narwhals
    try:
        return dataframe_to_records(data)
    except Exception as err:
        raise TypeError(
            f"Unsupported data type: {type(data).__name__}. "
            "Expected DataFrame, GeoDataFrame, DuckDB Relation, "
            "list of dicts, dict (GeoJSON), or str (URL)."
        ) from err


def dataframe_to_records(data: Any) -> list[dict]:
    """Convert a DataFrame to a list of dicts via narwhals.

    Parameters
    ----------
    data
        A pandas or polars DataFrame.

    Returns
    -------
    list[dict]
        List of row dictionaries.
    """
    df = nw.from_native(data)
    columns = df.columns
    result = []
    col_data = {col: df[col].to_list() for col in columns}
    n_rows = len(col_data[columns[0]]) if columns else 0
    for i in range(n_rows):
        result.append({col: col_data[col][i] for col in columns})
    return result


def dataframe_to_positions(
    data: Any,
    lat_col: str = "lat",
    lon_col: str = "lon",
) -> list[list[float]]:
    """Convert a DataFrame or list of dicts to [[lon, lat], ...] pairs.

    Parameters
    ----------
    data
        A pandas DataFrame, polars DataFrame, or list of dicts.
    lat_col
        Name of the latitude column.
    lon_col
        Name of the longitude column.

    Returns
    -------
    list[list[float]]
        Coordinate pairs as [[lon, lat], ...] for deck.gl.
    """
    if isinstance(data, list):
        return [[row[lon_col], row[lat_col]] for row in data]

    df = nw.from_native(data)
    lons = df[lon_col].to_list()
    lats = df[lat_col].to_list()
    return [[lon, lat] for lon, lat in zip(lons, lats, strict=True)]


def materialize_rows(data: Any) -> list[dict] | None:
    """Convert layer data to a list of row dicts for callable accessors.

    Returns ``None`` if data cannot be materialized (e.g., URL string).

    Parameters
    ----------
    data
        Raw layer data: DataFrame, GeoDataFrame, list of dicts,
        GeoJSON dict, DuckDB Relation, URL string, or None.

    Returns
    -------
    list[dict] | None
        Row dicts, or None for URL/None data.
    """
    if data is None:
        return None

    if isinstance(data, str):
        return None

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        # GeoJSON FeatureCollection: rows are the feature properties.
        # Any other plain dict has no row structure to materialize.
        if "features" in data:
            return [f.get("properties", {}) for f in data["features"]]
        return None

    # DuckDB Relation
    if hasattr(data, "fetchdf"):
        return materialize_rows(data.fetchdf())

    # GeoDataFrame — extract properties (non-geometry columns)
    if hasattr(data, "__geo_interface__") and hasattr(data, "columns"):
        geo = data.__geo_interface__
        return [f.get("properties", {}) for f in geo.get("features", [])]

    # pandas/polars DataFrame via narwhals
    try:
        return dataframe_to_records(data)
    except Exception:
        return None


def geodataframe_to_geojson(gdf: Any) -> dict:
    """Convert a GeoDataFrame to a GeoJSON FeatureCollection.

    Uses the ``__geo_interface__`` protocol, which is supported by
    geopandas GeoDataFrames.

    Parameters
    ----------
    gdf
        A GeoDataFrame with ``__geo_interface__`` attribute.

    Returns
    -------
    dict
        GeoJSON FeatureCollection dict.
    """
    return gdf.__geo_interface__
