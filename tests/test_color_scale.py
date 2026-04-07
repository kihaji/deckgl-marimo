"""Tests for ColorScale and callable accessor support."""

import math

import pytest

from deckgl_marimo._color_scale import (
    ColorScale,
    _extract_column,
    _interpolate_palette,
    _parse_color,
    resolve_color_accessor,
)
from deckgl_marimo._data import materialize_rows


# ---------------------------------------------------------------------------
# _parse_color
# ---------------------------------------------------------------------------

class TestParseColor:
    def test_named_color(self):
        assert _parse_color("blue") == [0, 0, 255]

    def test_named_color_case_insensitive(self):
        assert _parse_color("Blue") == [0, 0, 255]

    def test_hex_6(self):
        assert _parse_color("#FF8000") == [255, 128, 0]

    def test_hex_3(self):
        assert _parse_color("#F00") == [255, 0, 0]

    def test_rgb_list(self):
        assert _parse_color([10, 20, 30]) == [10, 20, 30]

    def test_rgb_tuple(self):
        assert _parse_color((10, 20, 30)) == [10, 20, 30]

    def test_invalid_string(self):
        with pytest.raises(ValueError, match="Cannot parse color"):
            _parse_color("not_a_color")


# ---------------------------------------------------------------------------
# _interpolate_palette
# ---------------------------------------------------------------------------

class TestInterpolatePalette:
    def test_two_colors(self):
        ramp = _interpolate_palette([[0, 0, 0], [255, 255, 255]], 3)
        assert len(ramp) == 3
        assert ramp[0] == [0, 0, 0]
        assert ramp[1] == [128, 128, 128]  # midpoint
        assert ramp[2] == [255, 255, 255]

    def test_single_output(self):
        ramp = _interpolate_palette([[0, 0, 0], [255, 255, 255]], 1)
        assert len(ramp) == 1

    def test_empty(self):
        assert _interpolate_palette([[0, 0, 0], [255, 255, 255]], 0) == []


# ---------------------------------------------------------------------------
# _extract_column
# ---------------------------------------------------------------------------

class TestExtractColumn:
    def test_list_of_dicts(self):
        data = [{"a": 1}, {"a": 2}, {"a": 3}]
        assert _extract_column(data, "a") == [1, 2, 3]

    def test_geojson(self):
        data = {
            "type": "FeatureCollection",
            "features": [
                {"properties": {"val": 10}},
                {"properties": {"val": 20}},
            ],
        }
        assert _extract_column(data, "val") == [10, 20]

    def test_url_raises(self):
        with pytest.raises(ValueError, match="URL data"):
            _extract_column("https://example.com/data.csv", "col")

    def test_none_returns_empty(self):
        assert _extract_column(None, "col") == []


# ---------------------------------------------------------------------------
# materialize_rows
# ---------------------------------------------------------------------------

class TestMaterializeRows:
    def test_list_of_dicts(self):
        data = [{"a": 1}, {"a": 2}]
        assert materialize_rows(data) is data

    def test_geojson(self):
        data = {
            "type": "FeatureCollection",
            "features": [
                {"properties": {"val": 10}},
                {"properties": {"val": 20}},
            ],
        }
        rows = materialize_rows(data)
        assert rows == [{"val": 10}, {"val": 20}]

    def test_url_returns_none(self):
        assert materialize_rows("https://example.com") is None

    def test_none_returns_none(self):
        assert materialize_rows(None) is None


# ---------------------------------------------------------------------------
# ColorScale.__init__ validation
# ---------------------------------------------------------------------------

class TestColorScaleValidation:
    def test_colors_and_palette_raises(self):
        with pytest.raises(ValueError, match="not both"):
            ColorScale("col", colors=["blue", "red"], palette="viridis")

    def test_neither_colors_nor_palette_raises(self):
        with pytest.raises(ValueError, match="Must specify"):
            ColorScale("col")

    def test_single_color_raises(self):
        with pytest.raises(ValueError, match="at least 2"):
            ColorScale("col", colors=["blue"])

    def test_unknown_palette_raises(self):
        with pytest.raises(ValueError, match="Unknown palette"):
            ColorScale("col", palette="nonexistent")

    def test_invalid_scale_raises(self):
        with pytest.raises(ValueError, match="Unknown scale"):
            ColorScale("col", colors=["blue", "red"], scale="quadratic")


# ---------------------------------------------------------------------------
# ColorScale.resolve — linear
# ---------------------------------------------------------------------------

class TestColorScaleResolveLinear:
    def test_two_colors_blue_to_red(self):
        data = [{"v": 0}, {"v": 50}, {"v": 100}]
        cs = ColorScale("v", colors=["blue", "red"])
        result = cs.resolve(data)
        assert len(result) == 3
        # Lowest value -> blue-ish
        assert result[0][2] > result[0][0]  # more blue than red
        # Highest value -> red-ish
        assert result[2][0] > result[2][2]  # more red than blue
        # Alpha
        assert result[0][3] == 255

    def test_named_palette(self):
        data = [{"v": i} for i in range(10)]
        cs = ColorScale("v", palette="viridis")
        result = cs.resolve(data)
        assert len(result) == 10
        assert all(len(c) == 4 for c in result)

    def test_explicit_domain(self):
        data = [{"v": 50}]
        cs = ColorScale("v", colors=["black", "white"], domain=(0, 100))
        result = cs.resolve(data)
        # 50 is midpoint, so gray-ish
        assert 100 < result[0][0] < 200

    def test_auto_domain(self):
        data = [{"v": 10}, {"v": 20}]
        cs = ColorScale("v", colors=["black", "white"])
        result = cs.resolve(data)
        # min=10 maps to black, max=20 maps to white
        assert result[0][0] < 10  # near black
        assert result[1][0] > 245  # near white

    def test_constant_domain_no_crash(self):
        data = [{"v": 5}, {"v": 5}, {"v": 5}]
        cs = ColorScale("v", colors=["blue", "red"])
        result = cs.resolve(data)
        assert len(result) == 3
        # All same value -> midpoint color
        assert result[0] == result[1] == result[2]

    def test_nan_handling(self):
        data = [{"v": 0}, {"v": float("nan")}, {"v": 100}]
        cs = ColorScale("v", colors=["blue", "red"])
        result = cs.resolve(data)
        assert result[1] == [0, 0, 0, 0]  # transparent

    def test_none_handling(self):
        data = [{"v": 0}, {"v": None}, {"v": 100}]
        cs = ColorScale("v", colors=["blue", "red"])
        result = cs.resolve(data)
        assert result[1] == [0, 0, 0, 0]

    def test_empty_data(self):
        cs = ColorScale("v", colors=["blue", "red"])
        assert cs.resolve([]) == []

    def test_custom_alpha(self):
        data = [{"v": 0}, {"v": 100}]
        cs = ColorScale("v", colors=["blue", "red"], alpha=128)
        result = cs.resolve(data)
        assert result[0][3] == 128
        assert result[1][3] == 128

    def test_evenly_spaced_linear(self):
        """Evenly spaced input values should produce evenly spaced color indices."""
        data = [{"v": i * 10} for i in range(11)]  # 0, 10, ..., 100
        cs = ColorScale("v", colors=["black", "white"])
        result = cs.resolve(data)
        # Red channel should increase monotonically
        reds = [c[0] for c in result]
        for i in range(len(reds) - 1):
            assert reds[i] <= reds[i + 1]


# ---------------------------------------------------------------------------
# ColorScale.resolve — log
# ---------------------------------------------------------------------------

class TestColorScaleResolveLog:
    def test_log_compresses_high_end(self):
        """Log scale should spread out low values more than high values."""
        data = [{"v": 0}, {"v": 50}, {"v": 100}]
        cs_linear = ColorScale("v", colors=["black", "white"], scale="linear")
        cs_log = ColorScale("v", colors=["black", "white"], scale="log")

        linear_result = cs_linear.resolve(data)
        log_result = cs_log.resolve(data)

        # Mid value (50) should be brighter (higher index) in log than linear
        assert log_result[1][0] > linear_result[1][0]

    def test_log_basic(self):
        data = [{"v": 1}, {"v": 10}, {"v": 100}, {"v": 1000}]
        cs = ColorScale("v", colors=["blue", "red"], scale="log")
        result = cs.resolve(data)
        assert len(result) == 4
        # Monotonically increasing red channel
        reds = [c[0] for c in result]
        for i in range(len(reds) - 1):
            assert reds[i] <= reds[i + 1]


# ---------------------------------------------------------------------------
# ColorScale.resolve_numpy
# ---------------------------------------------------------------------------

class TestColorScaleResolveNumpy:
    def test_matches_resolve(self):
        data = [{"v": 0}, {"v": 50}, {"v": 100}]
        cs = ColorScale("v", palette="viridis")
        list_result = cs.resolve(data)
        np_result = cs.resolve_numpy(data)
        assert np_result.shape == (3, 4)
        assert np_result.dtype.name == "uint8"
        for i in range(3):
            assert list(np_result[i]) == list_result[i]

    def test_empty(self):
        cs = ColorScale("v", colors=["blue", "red"])
        result = cs.resolve_numpy([])
        assert result.shape == (0, 4)


# ---------------------------------------------------------------------------
# resolve_color_accessor
# ---------------------------------------------------------------------------

class TestResolveColorAccessor:
    def test_color_scale(self):
        cs = ColorScale("v", colors=["blue", "red"])
        data = [{"v": 0}, {"v": 100}]
        result = resolve_color_accessor(cs, data, 2)
        assert result is not None
        assert result.shape == (2, 4)

    def test_callable(self):
        fn = lambda row: [row["v"], 0, 255 - row["v"], 200]
        data = [{"v": 0}, {"v": 100}]
        result = resolve_color_accessor(fn, data, 2)
        assert result is not None
        assert list(result[0]) == [0, 0, 255, 200]
        assert list(result[1]) == [100, 0, 155, 200]

    def test_string_returns_none(self):
        assert resolve_color_accessor("color_col", [{}], 1) is None

    def test_static_list_returns_none(self):
        assert resolve_color_accessor([255, 0, 0], [{}], 1) is None


# ---------------------------------------------------------------------------
# Integration: ScatterplotLayer + ColorScale (JSON path)
# ---------------------------------------------------------------------------

class TestScatterplotLayerColorScale:
    def test_to_spec_with_color_scale(self):
        from deckgl_marimo.layers._core import ScatterplotLayer

        data = [
            {"lon": -122.4, "lat": 37.8, "temp": 0},
            {"lon": -122.3, "lat": 37.7, "temp": 50},
            {"lon": -122.2, "lat": 37.6, "temp": 100},
        ]
        cs = ColorScale("temp", colors=["blue", "red"])
        layer = ScatterplotLayer(
            data=data,
            get_position=["lon", "lat"],
            get_fill_color=cs,
        )
        spec = layer.to_spec()
        fill = spec["getFillColor"]
        assert isinstance(fill, list)
        assert len(fill) == 3
        assert len(fill[0]) == 4

    def test_to_spec_with_callable(self):
        from deckgl_marimo.layers._core import ScatterplotLayer

        data = [
            {"lon": -122.4, "lat": 37.8, "temp": 50},
            {"lon": -122.3, "lat": 37.7, "temp": 100},
        ]
        layer = ScatterplotLayer(
            data=data,
            get_position=["lon", "lat"],
            get_fill_color=lambda row: [row["temp"], 0, 255 - row["temp"], 200],
        )
        spec = layer.to_spec()
        fill = spec["getFillColor"]
        assert fill == [[50, 0, 205, 200], [100, 0, 155, 200]]


# ---------------------------------------------------------------------------
# Integration: ScatterplotLayer + ColorScale (binary path)
# ---------------------------------------------------------------------------

class TestScatterplotLayerColorScaleBinary:
    def test_to_binary_with_color_scale(self):
        from deckgl_marimo.layers._core import ScatterplotLayer

        data = [
            {"lon": -122.4, "lat": 37.8, "temp": 0},
            {"lon": -122.3, "lat": 37.7, "temp": 50},
            {"lon": -122.2, "lat": 37.6, "temp": 100},
        ]
        cs = ColorScale("temp", colors=["blue", "red"])
        layer = ScatterplotLayer(
            data=data,
            get_position=["lon", "lat"],
            get_fill_color=cs,
            use_binary=True,
        )
        result = layer.to_binary()
        assert result is not None
        meta, buf = result
        assert "getFillColor" in meta["attributes"]
        assert meta["attributes"]["getFillColor"]["dtype"] == "uint8"
        assert meta["attributes"]["getFillColor"]["size"] == 4

    def test_to_spec_strips_resolved_colors_in_binary_mode(self):
        from deckgl_marimo.layers._core import ScatterplotLayer

        data = [
            {"lon": -122.4, "lat": 37.8, "temp": 0},
            {"lon": -122.3, "lat": 37.7, "temp": 100},
        ]
        cs = ColorScale("temp", colors=["blue", "red"])
        layer = ScatterplotLayer(
            data=data,
            get_position=["lon", "lat"],
            get_fill_color=cs,
            use_binary=True,
        )
        spec = layer.to_spec()
        # Resolved per-row arrays should be stripped since binary handles them
        assert "getFillColor" not in spec


# ---------------------------------------------------------------------------
# Integration: PolygonLayer + ColorScale (binary path)
# ---------------------------------------------------------------------------

class TestPolygonLayerColorScaleBinary:
    def test_to_binary_with_color_scale(self):
        from deckgl_marimo.layers._core import PolygonLayer

        data = [
            {"polygon": [[0, 0], [1, 0], [1, 1], [0, 1]], "val": 10},
            {"polygon": [[2, 2], [3, 2], [3, 3], [2, 3]], "val": 90},
        ]
        cs = ColorScale("val", palette="viridis")
        layer = PolygonLayer(
            data=data,
            get_polygon="polygon",
            get_fill_color=cs,
            use_binary=True,
        )
        result = layer.to_binary()
        assert result is not None
        meta, buf = result
        assert "getFillColor" in meta["attributes"]


# ---------------------------------------------------------------------------
# Regression: existing behavior unchanged
# ---------------------------------------------------------------------------

class TestExistingBehaviorUnchanged:
    def test_static_color(self):
        from deckgl_marimo.layers._core import ScatterplotLayer

        layer = ScatterplotLayer(
            data=[{"lon": 0, "lat": 0}],
            get_position=["lon", "lat"],
            get_fill_color=[255, 0, 0],
        )
        spec = layer.to_spec()
        assert spec["getFillColor"] == [255, 0, 0]

    def test_column_name(self):
        from deckgl_marimo.layers._core import ScatterplotLayer

        data = [{"lon": 0, "lat": 0, "color": [255, 128, 0]}]
        layer = ScatterplotLayer(
            data=data,
            get_position=["lon", "lat"],
            get_fill_color="color",
        )
        spec = layer.to_spec()
        assert spec["getFillColor"] == "color"

    def test_binary_with_string_column(self):
        from deckgl_marimo.layers._core import ScatterplotLayer

        data = [
            {"lon": -122.4, "lat": 37.8, "color": [255, 0, 0, 255]},
            {"lon": -122.3, "lat": 37.7, "color": [0, 255, 0, 255]},
        ]
        layer = ScatterplotLayer(
            data=data,
            get_position=["lon", "lat"],
            get_fill_color="color",
            use_binary=True,
        )
        result = layer.to_binary()
        assert result is not None
        meta, buf = result
        assert "getFillColor" in meta["attributes"]


# ---------------------------------------------------------------------------
# GeoJSON data support
# ---------------------------------------------------------------------------

class TestColorScaleGeoJSON:
    def test_resolve_geojson(self):
        data = {
            "type": "FeatureCollection",
            "features": [
                {"properties": {"temp": 0}},
                {"properties": {"temp": 50}},
                {"properties": {"temp": 100}},
            ],
        }
        cs = ColorScale("temp", colors=["blue", "red"])
        result = cs.resolve(data)
        assert len(result) == 3
        assert result[0][2] > result[0][0]  # blue-ish
        assert result[2][0] > result[2][2]  # red-ish
