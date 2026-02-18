"""DataFrame to positions conversion using narwhals."""

from __future__ import annotations

from typing import Any

import narwhals as nw


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
    return [[lon, lat] for lon, lat in zip(lons, lats)]
