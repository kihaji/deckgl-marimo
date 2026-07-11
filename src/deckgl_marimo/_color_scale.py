"""Color scale utilities for mapping numeric data to colors."""

from __future__ import annotations

import math
from typing import Any

import narwhals as nw


# Common CSS color names → RGB
_NAMED_COLORS: dict[str, list[int]] = {
    "red": [255, 0, 0],
    "green": [0, 128, 0],
    "blue": [0, 0, 255],
    "yellow": [255, 255, 0],
    "orange": [255, 165, 0],
    "purple": [128, 0, 128],
    "cyan": [0, 255, 255],
    "magenta": [255, 0, 255],
    "white": [255, 255, 255],
    "black": [0, 0, 0],
    "gray": [128, 128, 128],
    "grey": [128, 128, 128],
    "pink": [255, 192, 203],
    "brown": [165, 42, 42],
    "lime": [0, 255, 0],
    "navy": [0, 0, 128],
    "teal": [0, 128, 128],
    "maroon": [128, 0, 0],
    "olive": [128, 128, 0],
    "coral": [255, 127, 80],
    "salmon": [250, 128, 114],
    "gold": [255, 215, 0],
    "indigo": [75, 0, 130],
    "violet": [238, 130, 238],
    "turquoise": [64, 224, 208],
}

# Bundled palettes: list of RGB control points sampled from matplotlib references.
_PALETTES: dict[str, list[list[int]]] = {
    "viridis": [
        [68, 1, 84], [72, 40, 120], [62, 74, 137], [49, 104, 142],
        [38, 130, 142], [31, 158, 137], [53, 183, 121], [109, 205, 89],
        [180, 222, 44], [253, 231, 37],
    ],
    "plasma": [
        [13, 8, 135], [75, 3, 161], [125, 3, 168], [168, 34, 150],
        [203, 70, 121], [229, 107, 93], [248, 148, 65], [253, 195, 40],
        [240, 249, 33],
    ],
    "inferno": [
        [0, 0, 4], [22, 11, 57], [66, 10, 104], [106, 23, 110],
        [147, 38, 103], [188, 55, 84], [221, 81, 58], [243, 120, 25],
        [252, 172, 12], [252, 255, 164],
    ],
    "magma": [
        [0, 0, 4], [18, 13, 55], [51, 16, 104], [90, 17, 126],
        [130, 26, 128], [170, 42, 118], [208, 68, 100], [237, 105, 80],
        [251, 155, 64], [252, 253, 191],
    ],
    "cividis": [
        [0, 32, 77], [0, 55, 101], [42, 76, 108], [76, 96, 108],
        [108, 117, 110], [141, 137, 110], [175, 159, 100], [210, 182, 79],
        [247, 210, 42], [253, 231, 37],
    ],
    "coolwarm": [
        [59, 76, 192], [98, 130, 234], [141, 176, 254], [184, 208, 249],
        [221, 221, 221], [245, 196, 173], [241, 152, 123], [222, 96, 77],
        [180, 4, 38],
    ],
    "RdBu": [
        [103, 0, 31], [178, 24, 43], [214, 96, 77], [244, 165, 130],
        [247, 247, 247], [146, 197, 222], [67, 147, 195], [33, 102, 172],
        [5, 48, 97],
    ],
    "spectral": [
        [158, 1, 66], [213, 62, 79], [244, 109, 67], [253, 174, 97],
        [254, 254, 139], [230, 245, 152], [171, 221, 164], [102, 194, 165],
        [50, 136, 189], [94, 79, 162],
    ],
    "turbo": [
        [48, 18, 59], [86, 91, 214], [29, 162, 236], [23, 214, 163],
        [94, 241, 82], [185, 237, 47], [243, 195, 46], [253, 128, 37],
        [222, 52, 24], [122, 4, 3],
    ],
}

_VALID_SCALES = {"linear", "log"}


def _parse_color(color: str | list[int]) -> list[int]:
    """Parse a color string or RGB list to [R, G, B]."""
    if isinstance(color, (list, tuple)):
        return list(color[:3])
    if isinstance(color, str):
        lower = color.strip().lower()
        if lower in _NAMED_COLORS:
            return list(_NAMED_COLORS[lower])
        # Hex color
        hex_str = lower.lstrip("#")
        if len(hex_str) == 6:
            return [int(hex_str[i:i+2], 16) for i in (0, 2, 4)]
        if len(hex_str) == 3:
            return [int(c*2, 16) for c in hex_str]
    raise ValueError(f"Cannot parse color: {color!r}")


def _interpolate_palette(control_points: list[list[int]], n: int) -> list[list[int]]:
    """Linearly interpolate between control points to produce n RGB colors."""
    if n <= 0:
        return []
    if n == 1:
        return [list(control_points[len(control_points) // 2])]

    num_segments = len(control_points) - 1
    result = []
    for i in range(n):
        t = i / (n - 1)  # 0.0 to 1.0
        seg_float = t * num_segments
        seg_idx = min(int(seg_float), num_segments - 1)
        seg_t = seg_float - seg_idx

        c0 = control_points[seg_idx]
        c1 = control_points[seg_idx + 1]
        result.append([
            int(c0[0] + (c1[0] - c0[0]) * seg_t + 0.5),
            int(c0[1] + (c1[1] - c0[1]) * seg_t + 0.5),
            int(c0[2] + (c1[2] - c0[2]) * seg_t + 0.5),
        ])
    return result


def _extract_column(data: Any, column: str) -> list[float | None]:
    """Extract a numeric column from various data types."""
    if data is None:
        return []

    if isinstance(data, str):
        raise ValueError(
            f"ColorScale cannot extract column '{column}' from URL data. "
            "Provide actual data (DataFrame, list of dicts, etc.) or pre-compute colors."
        )

    if isinstance(data, list):
        return [row.get(column) if isinstance(row, dict) else None for row in data]

    if isinstance(data, dict):
        # GeoJSON FeatureCollection
        if "features" in data:
            return [f.get("properties", {}).get(column) for f in data["features"]]
        raise TypeError(
            f"Cannot extract column '{column}' from a plain dict. "
            "Expected DataFrame, list of dicts, GeoJSON dict, or GeoDataFrame."
        )

    # GeoDataFrame
    if hasattr(data, "__geo_interface__") and hasattr(data, "columns"):
        if column in data.columns:
            return data[column].tolist()
        raise KeyError(f"Column '{column}' not found in GeoDataFrame")

    # DuckDB Relation
    if hasattr(data, "fetchdf"):
        return _extract_column(data.fetchdf(), column)

    # pandas/polars via narwhals
    try:
        df = nw.from_native(data)
        return df[column].to_list()
    except Exception as err:
        raise TypeError(
            f"Cannot extract column '{column}' from {type(data).__name__}. "
            "Expected DataFrame, list of dicts, GeoJSON dict, or GeoDataFrame."
        ) from err


class ColorScale:
    """Map a numeric data column to interpolated colors.

    Produces per-row RGBA color arrays by mapping values from a numeric
    column through a color ramp. Use with any ``get_*_color`` accessor.

    Parameters
    ----------
    column
        Name of the numeric column to map.
    colors
        List of 2+ colors to interpolate between. Each color can be a
        CSS name (``"blue"``), hex string (``"#FF0000"``), or RGB list
        (``[255, 0, 0]``). Mutually exclusive with ``palette``.
    palette
        Name of a built-in palette. Available: ``"viridis"``,
        ``"plasma"``, ``"inferno"``, ``"magma"``, ``"cividis"``,
        ``"coolwarm"``, ``"RdBu"``, ``"spectral"``, ``"turbo"``.
        Mutually exclusive with ``colors``.
    domain
        ``(min, max)`` value range. If ``None``, auto-detected from data.
    scale
        Scale type: ``"linear"`` (default) or ``"log"``.
    alpha
        Alpha channel value (0-255) for all output colors.

    Examples
    --------
    >>> layer = ScatterplotLayer(
    ...     data=df,
    ...     get_fill_color=ColorScale("temperature", palette="viridis"),
    ... )

    >>> layer = ScatterplotLayer(
    ...     data=df,
    ...     get_fill_color=ColorScale("value", colors=["blue", "red"], scale="log"),
    ... )

    Notes
    -----
    ``ColorScale`` requires materialized data. If the layer's ``data``
    is a URL string, :meth:`resolve` raises ``ValueError`` — load the
    URL into a DataFrame or list of dicts first, or pre-compute colors
    and pass them as a regular column.
    """

    def __init__(
        self,
        column: str,
        *,
        colors: list[str | list[int]] | None = None,
        palette: str | None = None,
        domain: tuple[float, float] | None = None,
        scale: str = "linear",
        alpha: int = 255,
    ) -> None:
        if colors is not None and palette is not None:
            raise ValueError("Specify either 'colors' or 'palette', not both.")
        if colors is None and palette is None:
            raise ValueError("Must specify either 'colors' or 'palette'.")
        if colors is not None and len(colors) < 2:
            raise ValueError("'colors' must have at least 2 entries.")
        if palette is not None and palette not in _PALETTES:
            raise ValueError(
                f"Unknown palette '{palette}'. "
                f"Available: {', '.join(sorted(_PALETTES))}"
            )
        if scale not in _VALID_SCALES:
            raise ValueError(
                f"Unknown scale '{scale}'. Available: {', '.join(sorted(_VALID_SCALES))}"
            )

        self.column = column
        self.domain = domain
        self.scale = scale
        self.alpha = alpha

        # Build the color ramp (256 RGB entries)
        if palette is not None:
            control_points = _PALETTES[palette]
        else:
            control_points = [_parse_color(c) for c in colors]  # type: ignore[union-attr]

        self._ramp = _interpolate_palette(control_points, 256)

    def _normalize(self, values: list[float | None]) -> list[float | None]:
        """Normalize values to [0, 1] using the configured scale and domain."""
        # Filter out None/NaN for domain calculation
        numeric = [v for v in values if v is not None and not (isinstance(v, float) and math.isnan(v))]

        if not numeric:
            return [None] * len(values)

        if self.domain is not None:
            vmin, vmax = self.domain
        else:
            vmin = min(numeric)
            vmax = max(numeric)

        result: list[float | None] = []

        if self.scale == "log":
            range_val = vmax - vmin
            log_range = math.log1p(range_val) if range_val > 0 else 1.0
            for v in values:
                if v is None or (isinstance(v, float) and math.isnan(v)):
                    result.append(None)
                else:
                    clamped = max(v, vmin)
                    t = math.log1p(clamped - vmin) / log_range if range_val > 0 else 0.5
                    result.append(max(0.0, min(1.0, t)))
        else:  # linear
            range_val = vmax - vmin
            for v in values:
                if v is None or (isinstance(v, float) and math.isnan(v)):
                    result.append(None)
                else:
                    t = (v - vmin) / range_val if range_val > 0 else 0.5
                    result.append(max(0.0, min(1.0, t)))

        return result

    def resolve(self, data: Any) -> list[list[int]]:
        """Resolve to per-row RGBA arrays for JSON transfer.

        Parameters
        ----------
        data
            Layer data (DataFrame, list of dicts, GeoJSON dict, etc.)

        Returns
        -------
        list[list[int]]
            Per-row ``[R, G, B, A]`` color arrays.
        """
        values = _extract_column(data, self.column)
        if not values:
            return []

        normalized = self._normalize(values)
        ramp = self._ramp
        n_colors = len(ramp)
        alpha = self.alpha
        transparent = [0, 0, 0, 0]

        result = []
        for t in normalized:
            if t is None:
                result.append(transparent)
            else:
                idx = min(int(t * (n_colors - 1) + 0.5), n_colors - 1)
                rgb = ramp[idx]
                result.append([rgb[0], rgb[1], rgb[2], alpha])
        return result

    def resolve_numpy(self, data: Any) -> Any:
        """Resolve to a numpy uint8 array of shape (n, 4) for binary transfer.

        Parameters
        ----------
        data
            Layer data (DataFrame, list of dicts, GeoJSON dict, etc.)

        Returns
        -------
        numpy.ndarray
            RGBA colors as uint8 array with shape ``(n, 4)``.
        """
        import numpy as np

        values = _extract_column(data, self.column)
        if not values:
            return np.empty((0, 4), dtype=np.uint8)

        normalized = self._normalize(values)
        ramp = self._ramp
        n_colors = len(ramp)
        alpha = self.alpha
        n = len(normalized)

        result = np.zeros((n, 4), dtype=np.uint8)
        for i, t in enumerate(normalized):
            if t is not None:
                idx = min(int(t * (n_colors - 1) + 0.5), n_colors - 1)
                rgb = ramp[idx]
                result[i] = [rgb[0], rgb[1], rgb[2], alpha]
            # None/NaN rows stay [0, 0, 0, 0]
        return result

    def __repr__(self) -> str:
        return f"ColorScale({self.column!r}, scale={self.scale!r})"


def resolve_color_accessor(
    key_value: Any, data: Any, n: int
) -> Any | None:
    """Resolve a color accessor to a numpy uint8 (n, 4) array for binary packing.

    Returns ``None`` if the accessor is not a ColorScale or callable
    (i.e., it's a static value or column name handled by the existing
    binary path).
    """
    import numpy as np

    if isinstance(key_value, ColorScale):
        return key_value.resolve_numpy(data)

    if callable(key_value):
        from deckgl_marimo._data import materialize_rows

        rows = materialize_rows(data)
        if rows is None:
            return None
        colors = np.array([key_value(row) for row in rows], dtype=np.uint8)
        if colors.ndim == 2 and colors.shape[1] == 3:
            colors = np.hstack([colors, np.full((n, 1), 255, dtype=np.uint8)])
        return colors

    return None
