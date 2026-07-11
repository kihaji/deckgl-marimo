"""Smoke tests for the experimental geo and mesh layer wrappers (#27).

Every class gets a construct + to_spec() round-trip: correct type tag,
camelCase prop conversion, the experimental warning, and tuple-color
normalization.
"""

import warnings

import pytest

from deckgl_marimo.layers._geo import (
    GreatCircleLayer,
    H3ClusterLayer,
    H3HexagonLayer,
    MVTLayer,
    QuadkeyLayer,
    S2Layer,
    TerrainLayer,
    Tile3DLayer,
    TileLayer,
    TripsLayer,
)
from deckgl_marimo.layers._mesh import ScenegraphLayer, SimpleMeshLayer

# (class, ctor kwargs, expected camelCase spec key/value pairs)
CASES = [
    (
        GreatCircleLayer,
        {"get_source_position": ["a_lon", "a_lat"], "get_source_color": (1, 2, 3, 4)},
        {"getSourcePosition": ["a_lon", "a_lat"], "getSourceColor": [1, 2, 3, 4]},
    ),
    (
        H3ClusterLayer,
        {"get_hexagons": "hexes", "get_fill_color": (10, 20, 30, 40)},
        {"getHexagons": "hexes", "getFillColor": [10, 20, 30, 40]},
    ),
    (
        H3HexagonLayer,
        {"get_hexagon": "hex", "extruded": True, "get_elevation": "height"},
        {"getHexagon": "hex", "extruded": True, "getElevation": "height"},
    ),
    (
        MVTLayer,
        {"data": "https://tiles.example.com/{z}/{x}/{y}.mvt", "get_line_width": 2},
        {"data": "https://tiles.example.com/{z}/{x}/{y}.mvt", "getLineWidth": 2},
    ),
    (
        QuadkeyLayer,
        {"get_quadkey": "qk"},
        {"getQuadkey": "qk"},
    ),
    (
        S2Layer,
        {"get_s2_token": "token"},
        {"getS2Token": "token"},
    ),
    (
        TerrainLayer,
        {"elevation_data": "https://e.example/{z}/{x}/{y}.png", "texture": "https://t.example/{z}/{x}/{y}.png"},
        {"elevationData": "https://e.example/{z}/{x}/{y}.png", "texture": "https://t.example/{z}/{x}/{y}.png"},
    ),
    (
        TileLayer,
        {"min_zoom": 3, "max_zoom": 17, "tile_size": 512},
        {"minZoom": 3, "maxZoom": 17, "tileSize": 512},
    ),
    (
        Tile3DLayer,
        {"data": "https://example.com/tileset.json"},
        {"data": "https://example.com/tileset.json"},
    ),
    (
        TripsLayer,
        {"get_path": "path", "get_timestamps": "ts", "trail_length": 60, "current_time": 5},
        {"getPath": "path", "getTimestamps": "ts", "trailLength": 60, "currentTime": 5},
    ),
    (
        SimpleMeshLayer,
        {"get_position": ["lon", "lat"], "get_color": (9, 8, 7, 6), "mesh": "mesh-url"},
        {"getPosition": ["lon", "lat"], "getColor": [9, 8, 7, 6], "mesh": "mesh-url"},
    ),
    (
        ScenegraphLayer,
        {"get_position": ["lon", "lat"], "scenegraph": "model.gltf", "size_scale": 2},
        {"getPosition": ["lon", "lat"], "scenegraph": "model.gltf", "sizeScale": 2},
    ),
]

IDS = [case[0].__name__ for case in CASES]


@pytest.mark.parametrize(("cls", "kwargs", "expected"), CASES, ids=IDS)
class TestGeoMeshSmoke:
    def test_warns_experimental(self, cls, kwargs, expected):
        with pytest.warns(UserWarning, match="experimental"):
            cls(**kwargs)

    def test_spec_round_trip(self, cls, kwargs, expected):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            layer = cls(**kwargs)
        spec = layer.to_spec()
        assert spec["type"] == cls.LAYER_TYPE
        assert spec["id"].startswith(cls.LAYER_TYPE)
        for key, value in expected.items():
            assert spec[key] == value, key
        # No snake_case keys leak into the spec
        assert not [k for k in spec if "_" in k]

    def test_unknown_prop_raises_with_suggestion(self, cls, kwargs, expected):
        first = next(iter(kwargs))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with pytest.raises(TypeError, match="Unknown property"):
                cls(**{first + "_typo": kwargs[first]})
