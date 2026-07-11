"""Tests for unknown-kwarg validation in BaseLayer subclasses."""

from __future__ import annotations

import warnings

import pytest

import deckgl_marimo as dgl
from deckgl_marimo._base import BaseLayer


class TestUnknownKwargs:
    def test_typo_raises_with_suggestion(self):
        with pytest.raises(TypeError, match="get_fillColor") as exc:
            dgl.ScatterplotLayer(get_fillColor=[255, 0, 0])
        assert "get_fill_color" in str(exc.value)
        assert "did you mean" in str(exc.value)

    def test_camel_case_typo_caught(self):
        with pytest.raises(TypeError, match="getFillColor") as exc:
            dgl.ScatterplotLayer(getFillColor=[255, 0, 0])
        assert "get_fill_color" in str(exc.value)

    def test_completely_unknown_no_suggestion(self):
        # No close match → message lists the key without 'did you mean'
        with pytest.raises(TypeError, match="totally_made_up_xyzzy") as exc:
            dgl.ScatterplotLayer(totally_made_up_xyzzy=42)
        assert "totally_made_up_xyzzy" in str(exc.value)

    def test_message_mentions_layer_class(self):
        with pytest.raises(TypeError, match="HexagonLayer"):
            dgl.HexagonLayer(get_positon=["lon", "lat"])  # typo intentional

    def test_unsafe_props_bypasses_validation(self):
        layer = dgl.ScatterplotLayer(_unsafe_props=True, totally_made_up=42)
        assert layer._props["totally_made_up"] == 42
        # _unsafe_props itself is consumed and not stored
        assert "_unsafe_props" not in layer._props

    def test_unsafe_props_does_not_appear_in_spec_extras(self):
        layer = dgl.ScatterplotLayer(_unsafe_props=True, my_custom_prop="hello")
        spec = layer.to_spec()
        assert spec["myCustomProp"] == "hello"


class TestMapKwargs:
    """Map validates init kwargs the same way BaseLayer does for layer props."""

    def test_singular_layer_typo_raises_with_suggestion(self):
        with pytest.raises(TypeError, match="layer") as exc:
            dgl.Map(layer=[dgl.ScatterplotLayer(get_position=["lon", "lat"])])
        msg = str(exc.value)
        assert "Map" in msg
        assert "layers" in msg
        assert "did you mean" in msg

    def test_unknown_kwarg_raises(self):
        with pytest.raises(TypeError, match="totally_made_up_xyzzy"):
            dgl.Map(totally_made_up_xyzzy=42)

    def test_layers_plural_still_works(self):
        m = dgl.Map(layers=[dgl.ScatterplotLayer(get_position=["lon", "lat"])])
        assert len(m.layer_specs) == 1

    def test_unsafe_props_bypasses_validation(self):
        # Pass-through kwargs are allowed when explicitly opted in.
        m = dgl.Map(layers=[], _unsafe_props=True)
        assert m.layer_specs == []


class TestBaseLayerStillUnvalidated:
    """BaseLayer is the catch-all and intentionally accepts arbitrary props."""

    def test_base_layer_accepts_unknown(self):
        layer = BaseLayer(elevation_scale=100, color_range=[[1, 2, 3]])
        spec = layer.to_spec()
        assert spec["elevationScale"] == 100


class TestCallableAccessorRegression:
    """Validation must not break the callable accessor materialization path."""

    def test_callable_get_position(self):
        layer = dgl.ScatterplotLayer(
            data=[{"x": 1.0, "y": 2.0}, {"x": 3.0, "y": 4.0}],
            get_position=lambda r: [r["x"], r["y"]],
        )
        spec = layer.to_spec()
        assert spec["getPosition"] == [[1.0, 2.0], [3.0, 4.0]]


# Minimal kwargs each public layer needs to instantiate without raising
# from non-validation code paths (e.g. EllipseLayer rejects missing center).
_PUBLIC_LAYER_KWARGS: dict[str, dict] = {
    "ArcLayer": {},
    "ColumnLayer": {},
    "GeoJsonLayer": {},
    "IconLayer": {},
    "LineLayer": {},
    "PathLayer": {},
    "PointCloudLayer": {},
    "PolygonLayer": {},
    "ScatterplotLayer": {},
    "SolidPolygonLayer": {},
    "TextLayer": {},
    "HeatmapLayer": {},
    "HexagonLayer": {},
    "DisplacementLayer": {},
    "EllipseLayer": {
        "data": [{"lon": 0.0, "lat": 0.0, "axis": 100.0}],
        "center": ["lon", "lat"],
        "major_axis": "axis",
    },
}


@pytest.mark.parametrize("class_name", list(_PUBLIC_LAYER_KWARGS))
def test_every_public_layer_instantiates(class_name: str):
    cls = getattr(dgl, class_name)
    with warnings.catch_warnings():
        # Some layers (LineLayer, PointCloudLayer, SolidPolygonLayer) emit an
        # @_experimental warning at instantiation; that is unrelated here.
        warnings.simplefilter("ignore")
        cls(**_PUBLIC_LAYER_KWARGS[class_name])
