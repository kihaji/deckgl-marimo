"""Tests for the WFS GetFeature URL builder."""

from urllib.parse import parse_qs, urlparse

import pytest

from deckgl_marimo.wfs import get_feature_url

URL = "https://host.example/geoserver/wfs"


def _params(url: str) -> dict[str, str]:
    return {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}


class TestGetFeatureUrl:
    def test_defaults_200(self):
        url = get_feature_url(URL, "topp:states")
        assert url.startswith(URL + "?")
        p = _params(url)
        assert p["SERVICE"] == "WFS"
        assert p["VERSION"] == "2.0.0"
        assert p["REQUEST"] == "GetFeature"
        assert p["typeNames"] == "topp:states"
        assert p["outputFormat"] == "application/json"
        assert p["srsName"] == "EPSG:4326"
        assert "typeName" not in p
        assert "BBOX" not in p

    @pytest.mark.parametrize("version", ["1.0.0", "1.1.0"])
    def test_legacy_versions_use_typename_and_maxfeatures(self, version):
        p = _params(get_feature_url(URL, "topp:states", version=version, max_features=10))
        assert p["VERSION"] == version
        assert p["typeName"] == "topp:states"
        assert p["maxFeatures"] == "10"
        assert "count" not in p

    def test_200_uses_count_and_start_index(self):
        p = _params(get_feature_url(URL, "topp:states", max_features=25, start_index=50))
        assert p["count"] == "25"
        assert p["startIndex"] == "50"

    def test_bbox_tuple_gets_crs_suffix(self):
        p = _params(get_feature_url(URL, "topp:states", bbox=(-110.5, 30.0, -80.25, 44.0)))
        assert p["BBOX"] == "-110.5,30.0,-80.25,44.0,EPSG:4326"

    def test_bbox_accepts_map_bounds_shape(self):
        # Same ((west, south), (east, north)) shape as Map.bounds / fit_bounds.
        p = _params(get_feature_url(URL, "topp:states", bbox=((-110.5, 30.0), (-80.25, 44.0)), srs="EPSG:3857"))
        assert p["BBOX"] == "-110.5,30.0,-80.25,44.0,EPSG:3857"
        assert p["srsName"] == "EPSG:3857"

    def test_bbox_bad_shape_raises(self):
        with pytest.raises(ValueError, match="bbox"):
            get_feature_url(URL, "topp:states", bbox=(1, 2, 3))

    def test_cql_filter_is_encoded(self):
        url = get_feature_url(URL, "topp:states", cql_filter="STATE_NAME = 'Texas'")
        assert _params(url)["CQL_FILTER"] == "STATE_NAME = 'Texas'"
        assert "CQL_FILTER=STATE_NAME+%3D+%27Texas%27" in url

    def test_property_names_sort_by_feature_ids(self):
        p = _params(get_feature_url(
            URL, "topp:states", property_names=["STATE_NAME", "the_geom"], sort_by="PERSONS DESC",
            feature_ids=["states.1", "states.2"],
        ))
        assert p["propertyName"] == "STATE_NAME,the_geom"
        assert p["sortBy"] == "PERSONS DESC"
        assert p["featureID"] == "states.1,states.2"

    def test_existing_query_params_preserved_but_not_overridden(self):
        url = get_feature_url(URL + "?map=/x.map&service=WMS", "ns:t")
        p = _params(url)
        assert p["map"] == "/x.map"
        assert p["SERVICE"] == "WFS"
        assert "service" not in p  # case-insensitive override

    def test_extra_params_win(self):
        p = _params(get_feature_url(URL, "ns:t", extra_params={"outputFormat": "GML2", "authkey": "abc"}))
        assert p["outputFormat"] == "GML2"
        assert p["authkey"] == "abc"

    def test_unknown_version_raises(self):
        with pytest.raises(ValueError, match="Unsupported WFS version"):
            get_feature_url(URL, "ns:t", version="3.0.0")
