"""GetFeature URL builder (pure; no network).

Mirrors :meth:`deckgl_marimo.maplibre.RasterSource.from_wms`: compose the
OGC query string in Python and let the browser (deck.gl / loaders.gl) or
:class:`~deckgl_marimo.wfs.WFSClient` fetch it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

SUPPORTED_VERSIONS = ("1.0.0", "1.1.0", "2.0.0")

BBox = tuple[float, float, float, float]


def _check_version(version: str) -> None:
    if version not in SUPPORTED_VERSIONS:
        raise ValueError(f"Unsupported WFS version {version!r}; expected one of {SUPPORTED_VERSIONS}")


def _normalize_bbox(bbox: object) -> BBox:
    """Accept ``(w, s, e, n)`` or ``((w, s), (e, n))`` (the ``Map.bounds`` shape)."""
    seq = list(bbox)  # type: ignore[call-overload]
    if len(seq) == 2:
        (west, south), (east, north) = seq
    elif len(seq) == 4:
        west, south, east, north = seq
    else:
        raise ValueError("bbox must be (west, south, east, north) or ((west, south), (east, north))")
    return (float(west), float(south), float(east), float(north))


def get_feature_url(
    url: str,
    typename: str,
    *,
    version: str = "2.0.0",
    bbox: object | None = None,
    cql_filter: str | None = None,
    max_features: int | None = None,
    start_index: int | None = None,
    srs: str = "EPSG:4326",
    property_names: Sequence[str] | None = None,
    sort_by: str | None = None,
    feature_ids: Sequence[str] | None = None,
    output_format: str = "application/json",
    extra_params: Mapping[str, str] | None = None,
) -> str:
    """Build a WFS ``GetFeature`` URL that returns GeoJSON.

    Parameters
    ----------
    url
        WFS endpoint (e.g. ``https://host/geoserver/wfs``). Existing query
        parameters are preserved unless overridden.
    typename
        Feature type, usually namespace-qualified (``"topp:states"``).
    version
        ``"1.0.0"``, ``"1.1.0"`` or ``"2.0.0"`` (parameter names differ).
    bbox
        Spatial filter as ``(west, south, east, north)`` or the
        ``((west, south), (east, north))`` shape of :attr:`Map.bounds`.
        Always sent with an explicit CRS suffix (``BBOX=w,s,e,n,EPSG:4326``)
        so axis order is unambiguous.
    cql_filter
        GeoServer vendor ``CQL_FILTER`` expression
        (``"STATE_NAME = 'Texas'"``).
    max_features
        Row cap (``count`` in 2.0.0, ``maxFeatures`` in 1.x).
    start_index
        Paging offset (``startIndex``).
    srs
        Output CRS (``srsName``); keep ``EPSG:4326`` for deck.gl.
    property_names
        Restrict returned attributes (``propertyName``).
    sort_by
        ``sortBy`` expression (``"POP DESC"``).
    feature_ids
        Fetch specific features by id (``featureID``).
    output_format
        Defaults to GeoJSON; change only if you know the server's formats.
    extra_params
        Additional query parameters (vendor options).
    """
    _check_version(version)
    params: dict[str, str] = {
        "SERVICE": "WFS",
        "VERSION": version,
        "REQUEST": "GetFeature",
        "typeNames" if version == "2.0.0" else "typeName": typename,
        "outputFormat": output_format,
        "srsName": srs,
    }
    if max_features is not None:
        params["count" if version == "2.0.0" else "maxFeatures"] = str(int(max_features))
    if start_index is not None:
        params["startIndex"] = str(int(start_index))
    if bbox is not None:
        west, south, east, north = _normalize_bbox(bbox)
        params["BBOX"] = f"{west},{south},{east},{north},{srs}"
    if cql_filter:
        params["CQL_FILTER"] = cql_filter
    if property_names:
        params["propertyName"] = ",".join(property_names)
    if sort_by:
        params["sortBy"] = sort_by
    if feature_ids:
        params["featureID"] = ",".join(feature_ids)
    if extra_params:
        params.update(extra_params)

    parsed = urlparse(url)
    lowered = {k.lower() for k in params}
    for key, value in parse_qs(parsed.query).items():
        if key.lower() not in lowered:
            params[key] = value[0] if value else ""

    query = urlencode(params, safe=",:")
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", query, ""))
