"""Tests for WFSLayer (GeoJsonLayer with a WFS GetFeature URL as data)."""

from urllib.parse import parse_qs, urlparse

import pytest

from deckgl_marimo import ColorScale, Map
from deckgl_marimo.wfs import WFSClient, WFSLayer

URL = "https://host.example/geoserver/wfs"


def _params(url: str) -> dict[str, str]:
    return {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}


class TestWFSLayerSpec:
    def test_data_is_getfeature_url(self):
        layer = WFSLayer(url=URL, typename="topp:states", id="states", max_features=100)
        spec = layer.to_spec()
        assert spec["type"] == "GeoJsonLayer"
        assert spec["id"] == "states"
        p = _params(spec["data"])
        assert p["typeNames"] == "topp:states"
        assert p["outputFormat"] == "application/json"
        assert p["count"] == "100"
        assert spec["data"] == layer.request_url

    def test_wfs_params_do_not_leak_into_deck_props(self):
        layer = WFSLayer(url=URL, typename="topp:states", bbox=(0, 0, 1, 1), cql_filter="a=1")
        spec = layer.to_spec()
        for junk in ("url", "typename", "bbox", "cqlFilter", "maxFeatures", "srs", "version"):
            assert junk not in spec

    def test_geojson_props_still_work(self):
        layer = WFSLayer(url=URL, typename="t", get_fill_color=(1, 2, 3, 4), line_width_min_pixels=2)
        spec = layer.to_spec()
        assert spec["getFillColor"] == [1, 2, 3, 4]
        assert spec["lineWidthMinPixels"] == 2

    def test_unknown_prop_raises(self):
        with pytest.raises(TypeError, match="Unknown property"):
            WFSLayer(url=URL, typename="t", get_fil_color=(1, 2, 3))

    def test_fetch_headers_passthrough(self):
        layer = WFSLayer(url=URL, typename="t", fetch_headers={"Authorization": "Bearer x"})
        assert layer.to_spec()["loadOptions"]["fetch"]["headers"] == {"Authorization": "Bearer x"}

    def test_color_scale_is_rejected_for_url_data(self):
        layer = WFSLayer(url=URL, typename="t", get_fill_color=ColorScale("POP", palette="viridis"))
        with pytest.raises(ValueError):
            layer.to_spec()

    def test_attribute_getters(self):
        layer = WFSLayer(url=URL, typename="t", version="1.1.0", bbox=(0, 0, 1, 1), property_names=("a", "b"))
        assert layer.url == URL
        assert layer.typename == "t"
        assert layer.version == "1.1.0"
        assert layer.bbox == (0, 0, 1, 1)
        assert layer.property_names == ["a", "b"]


class TestWFSLayerUpdate:
    def test_setters_rebuild_data(self):
        layer = WFSLayer(url=URL, typename="t")
        layer.bbox = ((-10, -5), (10, 5))
        assert _params(layer.data)["BBOX"] == "-10.0,-5.0,10.0,5.0,EPSG:4326"
        layer.cql_filter = "X > 1"
        layer.max_features = 7
        layer.typename = "ns:other"
        p = _params(layer.data)
        assert p["CQL_FILTER"] == "X > 1"
        assert p["count"] == "7"
        assert p["typeNames"] == "ns:other"

    def test_map_update_layer_regenerates_url(self):
        m = Map(layers=[WFSLayer(url=URL, typename="t", id="wfs")])
        m.update_layer("wfs", bbox=(-120, 30, -100, 45), max_features=50)
        spec = m.layer_specs[0]
        p = _params(spec["data"])
        assert p["BBOX"] == "-120.0,30.0,-100.0,45.0,EPSG:4326"
        assert p["count"] == "50"
        assert "bbox" not in spec and "maxFeatures" not in spec

    def test_map_update_layer_with_bounds_shape(self):
        m = Map(layers=[WFSLayer(url=URL, typename="t", id="wfs")])
        m.update_layer("wfs", bbox=((-120, 30), (-100, 45)))
        assert _params(m.layer_specs[0]["data"])["BBOX"].startswith("-120.0,30.0,-100.0,45.0")

    def test_map_update_layer_unknown_prop_still_raises(self):
        m = Map(layers=[WFSLayer(url=URL, typename="t", id="wfs")])
        with pytest.raises(TypeError, match="Unknown property"):
            m.update_layer("wfs", bbbox=(0, 0, 1, 1))


class TestFromClient:
    def test_copies_url_version_and_basic_auth(self):
        client = WFSClient(URL, version="1.1.0", auth=("u", "p"), headers={"X-Key": "k"})
        layer = WFSLayer.from_client(client, "ns:t", max_features=3)
        p = _params(layer.data)
        assert p["VERSION"] == "1.1.0"
        assert p["typeName"] == "ns:t"
        headers = layer.to_spec()["loadOptions"]["fetch"]["headers"]
        assert headers["X-Key"] == "k"
        assert headers["Authorization"] == "Basic dTpw"  # base64("u:p")

    def test_no_auth_no_headers(self):
        layer = WFSLayer.from_client(WFSClient(URL), "ns:t")
        assert "loadOptions" not in layer.to_spec()
