"""Tests for the maplibre composition module (#35)."""

import pytest

from deckgl_marimo import Map
from deckgl_marimo.maplibre import (
    CircleLayer,
    FillExtrusionLayer,
    FillLayer,
    GeoJSONSource,
    LineLayer,
    MapLibreConfig,
    RasterLayer,
    RasterSource,
    SymbolLayer,
    VectorSource,
    empty_style,
)


class TestRasterSource:
    def test_xyz_to_dict(self):
        src = RasterSource(tiles=["https://tile.example/{z}/{x}/{y}.png"], attribution="© x")
        assert src.to_dict() == {
            "type": "raster",
            "tiles": ["https://tile.example/{z}/{x}/{y}.png"],
            "tileSize": 256,
            "attribution": "© x",
        }

    def test_wms_url_template(self):
        src = RasterSource.from_wms(
            "https://ows.terrestris.de/osm/service", layers="TOPO-WMS"
        )
        url = src.to_dict()["tiles"][0]
        assert url.startswith("https://ows.terrestris.de/osm/service?")
        assert "SERVICE=WMS" in url
        assert "REQUEST=GetMap" in url
        assert "LAYERS=TOPO-WMS" in url
        assert "SRS=EPSG%3A3857" in url          # 1.1.1 uses SRS
        assert "BBOX={bbox-epsg-3857}" in url    # placeholder must stay literal
        assert "WIDTH=256" in url

    def test_wms_130_uses_crs(self):
        src = RasterSource.from_wms("https://w.example/wms", layers="l", version="1.3.0")
        url = src.to_dict()["tiles"][0]
        assert "CRS=EPSG%3A3857" in url
        assert "SRS=" not in url

    def test_wms_merges_existing_query_params(self):
        src = RasterSource.from_wms("https://w.example/wms?map=/maps/x.map", layers="l")
        url = src.to_dict()["tiles"][0]
        assert "MAP=%2Fmaps%2Fx.map" in url

    def test_wms_extra_params_and_kwargs(self):
        src = RasterSource.from_wms(
            "https://w.example/wms", layers="l",
            extra_params={"TILED": "TRUE"}, attribution="© wms", min_zoom=3,
        )
        d = src.to_dict()
        assert "TILED=TRUE" in d["tiles"][0]
        assert d["attribution"] == "© wms"
        assert d["minzoom"] == 3


class TestVectorAndGeoJSONSources:
    def test_vector_source(self):
        src = VectorSource(tiles=["https://t.example/{z}/{x}/{y}.pbf"], promote_id="fid")
        d = src.to_dict()
        assert d["type"] == "vector"
        assert d["promoteId"] == "fid"

    def test_vector_tilejson(self):
        assert VectorSource(url="https://t.example/tiles.json").to_dict()["url"]

    def test_geojson_source_with_clustering(self):
        src = GeoJSONSource(data="https://d.example/x.geojson", cluster=True, cluster_radius=80)
        d = src.to_dict()
        assert d["type"] == "geojson"
        assert d["cluster"] is True
        assert d["clusterRadius"] == 80


class TestMapLibreLayers:
    def test_kebab_case_paint_and_layout(self):
        layer = FillLayer(
            id="f", source="s", source_layer="buildings",
            fill_color="#f00", fill_opacity=0.5, visibility="visible",
        )
        d = layer.to_dict()
        assert d["type"] == "fill"
        assert d["source-layer"] == "buildings"
        assert d["paint"] == {"fill-color": "#f00", "fill-opacity": 0.5}
        assert d["layout"] == {"visibility": "visible"}

    def test_raster_layer(self):
        d = RasterLayer(id="r", source="wms", raster_opacity=0.7).to_dict()
        assert d == {"id": "r", "type": "raster", "source": "wms", "paint": {"raster-opacity": 0.7}}

    def test_zoom_and_filter(self):
        d = LineLayer(
            id="l", source="s", line_width=2,
            min_zoom=5, max_zoom=15, filter=["==", "class", "primary"],
        ).to_dict()
        assert d["minzoom"] == 5
        assert d["maxzoom"] == 15
        assert d["filter"] == ["==", "class", "primary"]

    def test_symbol_expression_values(self):
        d = SymbolLayer(id="t", source="s", text_field=["get", "name"], text_color="#000").to_dict()
        assert d["layout"]["text-field"] == ["get", "name"]
        assert d["paint"]["text-color"] == "#000"

    def test_circle_and_extrusion(self):
        assert CircleLayer(id="c", source="s", circle_radius=6).to_dict()["paint"]["circle-radius"] == 6
        d = FillExtrusionLayer(id="e", source="s", fill_extrusion_height=["get", "h"]).to_dict()
        assert d["type"] == "fill-extrusion"
        assert d["paint"]["fill-extrusion-height"] == ["get", "h"]

    def test_raw_paint_dict_merges(self):
        d = FillLayer(id="f", source="s", fill_color="#f00", paint={"fill-opacity": 0.1}).to_dict()
        assert d["paint"] == {"fill-opacity": 0.1, "fill-color": "#f00"}


class TestMapLibreConfig:
    def test_resolves_style_alias(self):
        cfg = MapLibreConfig(style="positron")
        assert cfg.to_dict()["style"].startswith("https://basemaps.cartocdn.com")

    def test_passes_url_and_inline_style(self):
        assert MapLibreConfig(style="https://x.example/s.json").to_dict()["style"] == "https://x.example/s.json"
        inline = empty_style()
        assert MapLibreConfig(style=inline).to_dict()["style"] == inline

    def test_serializes_objects_and_dicts(self):
        cfg = MapLibreConfig(
            style=empty_style(),
            sources={
                "wms": RasterSource(tiles=["https://t/{z}/{x}/{y}"]),
                "raw": {"type": "geojson", "data": {"type": "FeatureCollection", "features": []}},
            },
            map_layers=[RasterLayer(id="r", source="wms"), {"id": "raw-l", "type": "circle", "source": "raw"}],
            map_options={"maxPitch": 70},
        )
        d = cfg.to_dict()
        assert d["sources"]["wms"]["type"] == "raster"
        assert d["sources"]["raw"]["type"] == "geojson"
        assert [layer["id"] for layer in d["mapLayers"]] == ["r", "raw-l"]
        assert d["mapOptions"] == {"maxPitch": 70}


class TestMapIntegration:
    def test_map_accepts_config(self):
        cfg = MapLibreConfig(
            style="dark-matter",
            sources={"wms": RasterSource(tiles=["https://t/{z}/{x}/{y}"])},
            map_layers=[RasterLayer(id="r", source="wms")],
        )
        m = Map(basemap=cfg)
        assert m.maplibre_config["style"].startswith("https://basemaps.cartocdn.com")
        assert "wms" in m.maplibre_config["sources"]
        assert m.basemap_style == ""

    def test_map_accepts_inline_style_dict(self):
        m = Map(basemap=empty_style())
        assert m.maplibre_config["style"]["version"] == 8

    def test_map_accepts_config_dict(self):
        m = Map(basemap={"style": "positron", "sources": {}})
        assert m.maplibre_config["style"] == "positron"

    def test_plain_string_still_works(self):
        m = Map(basemap="dark-matter")
        assert m.basemap_style.startswith("https://basemaps.cartocdn.com")
        assert m.maplibre_config == {}

    def test_runtime_config_swap(self):
        m = Map(basemap="dark-matter")
        m.maplibre_config = MapLibreConfig(style="positron").to_dict()
        assert "positron" in m.maplibre_config["style"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
