"""Tests for the drawing configuration API (#37)."""

import pytest

from deckgl_marimo import (
    DRAWING_MODES,
    EMPTY_FEATURE_COLLECTION,
    DrawingConfig,
    DrawingStyle,
    Map,
)


class TestDrawingStyle:
    def test_color_normalization(self):
        style = DrawingStyle(
            fill_color="#ff8c00",
            line_color="black",
            tentative_fill_color=[255, 140, 0, 50],
            line_width=2,
            point_radius=8,
            show_measurements=False,
        )
        d = style.to_dict()
        assert d["fillColor"] == [255, 140, 0, 255]
        assert d["lineColor"] == [0, 0, 0, 255]
        assert d["tentativeFillColor"] == [255, 140, 0, 50]
        assert d["lineWidth"] == 2
        assert d["pointRadius"] == 8
        assert d["showMeasurements"] is False

    def test_rgb_gets_alpha(self):
        assert DrawingStyle(line_color=[1, 2, 3]).to_dict()["lineColor"] == [1, 2, 3, 255]

    def test_empty_style(self):
        assert DrawingStyle().to_dict() == {}


class TestDrawingConfig:
    def test_valid_modes(self):
        for mode in DRAWING_MODES:
            assert DrawingConfig(mode).to_dict()["mode"] == mode

    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError, match="Invalid drawing mode"):
            DrawingConfig("scribble")

    def test_full_config(self):
        cfg = DrawingConfig(
            "modify",
            selected_feature_indexes=[0, 2],
            style=DrawingStyle(fill_color=[1, 2, 3, 4]),
            delete_selected=True,
        )
        d = cfg.to_dict()
        assert d == {
            "mode": "modify",
            "selectedFeatureIndexes": [0, 2],
            "style": {"fillColor": [1, 2, 3, 4]},
            "deleteSelected": True,
        }

    def test_minimal_config_omits_empty_keys(self):
        assert DrawingConfig("draw_polygon").to_dict() == {"mode": "draw_polygon"}


class TestMapDrawing:
    def test_map_accepts_config_object_and_dict(self):
        m = Map(drawing_config=DrawingConfig("draw_polygon"))
        assert m.drawing_config == {"mode": "draw_polygon"}
        m2 = Map(drawing_config={"mode": "modify"})
        assert m2.drawing_config == {"mode": "modify"}

    def test_defaults(self):
        m = Map()
        assert m.drawing_config == {}
        assert m.drawing_features == EMPTY_FEATURE_COLLECTION
        assert m.drawing_event == {}

    def test_features_settable_from_python(self):
        m = Map()
        fc = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [1.0, 2.0]},
                "properties": {},
            }],
        }
        m.drawing_features = fc
        assert m.drawing_features["features"][0]["geometry"]["coordinates"] == [1.0, 2.0]

    def test_runtime_mode_switch(self):
        m = Map(drawing_config=DrawingConfig("draw_polygon"))
        m.drawing_config = DrawingConfig("delete").to_dict()
        assert m.drawing_config["mode"] == "delete"
