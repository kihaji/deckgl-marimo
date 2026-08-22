"""HTTP client for OGC WFS 1.0.0 / 1.1.0 / 2.0.0, including WFS-T transactions.

Uses ``requests`` (``pip install 'deckgl-marimo[wfs]'``), imported lazily so
the core package stays dependency-free. A ``requests.Session``-like object
(anything with ``.request(method, url, **kw)`` returning an object with
``status_code``/``content``) can be injected for custom auth or tests.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from deckgl_marimo.wfs._errors import WFSError
from deckgl_marimo.wfs._gml import normalize_gml_type
from deckgl_marimo.wfs._transaction import (
    FeatureTypeInfo,
    TransactionResult,
    UpdateSpec,
    build_transaction_xml,
    parse_transaction_response,
)
from deckgl_marimo.wfs._url import SUPPORTED_VERSIONS, get_feature_url
from deckgl_marimo.wfs._xml import (
    child_local,
    exception_from_report,
    first_local,
    iter_local,
    local_name,
    parse_xml,
)

_XMLNS_RE = re.compile(rb'xmlns:([A-Za-z_][\w.-]*)\s*=\s*"([^"]*)"')


@dataclass(frozen=True)
class Capabilities:
    """Subset of ``GetCapabilities`` relevant to reading/editing features."""

    version: str
    title: str = ""
    feature_types: list[str] = field(default_factory=list)
    operations: list[str] = field(default_factory=list)

    @property
    def supports_transaction(self) -> bool:
        """Whether the server advertises the WFS-T ``Transaction`` operation."""
        return "Transaction" in self.operations


class WFSClient:
    """Read features from a WFS and write them back with WFS-T transactions.

    Parameters
    ----------
    url
        Service endpoint, e.g. ``"https://host/geoserver/wfs"``.
    version
        ``"2.0.0"`` (default), ``"1.1.0"`` or ``"1.0.0"``. GeoServer supports
        all three; QGIS Server only transacts in 1.0.0.
    auth
        ``(user, password)`` for HTTP basic auth.
    headers
        Extra headers sent with every request (tokens, API keys).
    timeout
        Seconds per request.
    session
        Optional ``requests.Session``-like object; created lazily otherwise.
    axis_order
        How coordinates are written in transaction GML: ``"auto"`` swaps to
        lat/lon when ``srs_name`` is a URN-style identifier (GeoServer's
        behaviour for ``urn:ogc:def:crs:EPSG::4326``); ``"xy"`` never swaps;
        ``"yx"`` always swaps.
    srs_name
        ``srsName`` written in transaction GML. Defaults to
        ``urn:ogc:def:crs:EPSG::4326`` (1.1.0/2.0.0) or ``EPSG:4326`` (1.0.0).
        Features are always *read* as EPSG:4326 GeoJSON (lon/lat).

    Examples
    --------
    ::

        from deckgl_marimo.wfs import WFSClient

        wfs = WFSClient("http://localhost:8080/geoserver/wfs", auth=("admin", "geoserver"))
        fc = wfs.get_features("topp:tasmania_roads", bbox=m.bounds, max_features=500)
        result = wfs.update("topp:tasmania_roads", "tasmania_roads.1", properties={"TYPE": "highway"})
    """

    def __init__(
        self,
        url: str,
        *,
        version: str = "2.0.0",
        auth: tuple[str, str] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float = 30.0,
        session: Any = None,
        axis_order: str = "auto",
        srs_name: str | None = None,
    ) -> None:
        if version not in SUPPORTED_VERSIONS:
            raise ValueError(f"Unsupported WFS version {version!r}; expected one of {SUPPORTED_VERSIONS}")
        if axis_order not in ("auto", "xy", "yx"):
            raise ValueError("axis_order must be 'auto', 'xy' or 'yx'")
        self.url = url
        self.version = version
        self.auth = auth
        self.headers = dict(headers or {})
        self.timeout = timeout
        self.axis_order = axis_order
        self.srs_name = srs_name
        self._session = session
        self._ft_cache: dict[str, FeatureTypeInfo] = {}

    # ------------------------------------------------------------------ HTTP
    def _get_session(self) -> Any:
        if self._session is None:
            try:
                import requests
            except ImportError as exc:  # pragma: no cover - exercised via tests with a fake session
                raise ImportError(
                    "WFSClient needs the 'requests' package. Install it with: pip install 'deckgl-marimo[wfs]'"
                ) from exc
            self._session = requests.Session()
        return self._session

    def _request(self, method: str, url: str, *, data: bytes | None = None, content_type: str | None = None) -> bytes:
        headers = dict(self.headers)
        if content_type:
            headers["Content-Type"] = content_type
        kwargs: dict[str, Any] = {"headers": headers, "timeout": self.timeout}
        if self.auth is not None:
            kwargs["auth"] = self.auth
        if data is not None:
            kwargs["data"] = data
        try:
            resp = self._get_session().request(method, url, **kwargs)
        except Exception as exc:
            raise WFSError(f"WFS request failed: {exc}") from exc
        status = int(getattr(resp, "status_code", 0) or 0)
        body: bytes = resp.content if isinstance(resp.content, bytes) else str(resp.content).encode("utf-8")
        root = parse_xml(body)
        if root is not None:
            err = exception_from_report(root, status=status)
            if err is not None:
                raise err
        if status >= 400:
            raise WFSError(f"HTTP {status} from WFS: {body[:300].decode('utf-8', errors='replace')}", status=status)
        return body

    def _service_url(self, **params: str) -> str:
        from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

        parsed = urlparse(self.url)
        merged: dict[str, str] = {"SERVICE": "WFS", "VERSION": self.version, **params}
        lowered = {k.lower() for k in merged}
        for key, value in parse_qs(parsed.query).items():
            if key.lower() not in lowered:
                merged[key] = value[0] if value else ""
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", urlencode(merged, safe=",:"), ""))

    # ------------------------------------------------------------- requests
    def get_capabilities(self) -> Capabilities:
        """``GetCapabilities`` -> feature type names + advertised operations."""
        body = self._request("GET", self._service_url(REQUEST="GetCapabilities"))
        root = parse_xml(body)
        if root is None:
            raise WFSError("GetCapabilities did not return XML")
        title_el = first_local(root, "Title")
        feature_types: list[str] = []
        for ft in iter_local(root, "FeatureType"):
            name = child_local(ft, "Name")
            if name is not None and name.text:
                feature_types.append(name.text.strip())
        operations: list[str] = []
        for op in iter_local(root, "Operation"):
            name_attr = op.get("name")
            if name_attr:
                operations.append(name_attr)
        if not operations:  # WFS 1.0.0: <Capability><Request><GetFeature/>...
            request = first_local(root, "Request")
            if request is not None:
                operations = [local_name(child.tag) for child in request]
        version = root.get("version") or self.version
        return Capabilities(
            version=version,
            title=(title_el.text or "").strip() if title_el is not None else "",
            feature_types=feature_types,
            operations=sorted(set(operations)),
        )

    def describe_feature_type(self, typename: str) -> FeatureTypeInfo:
        """``DescribeFeatureType`` -> :class:`FeatureTypeInfo` (cached per typename)."""
        cached = self._ft_cache.get(typename)
        if cached is not None:
            return cached
        key = "typeNames" if self.version == "2.0.0" else "typeName"
        body = self._request("GET", self._service_url(REQUEST="DescribeFeatureType", **{key: typename}))
        info = parse_describe_feature_type(body, typename)
        self._ft_cache[typename] = info
        return info

    def get_feature_url(self, typename: str, **query: Any) -> str:
        """GetFeature URL for ``typename`` (see :func:`get_feature_url`)."""
        return get_feature_url(self.url, typename, version=self.version, **query)

    def get_features(self, typename: str, **query: Any) -> dict[str, Any]:
        """Fetch features as a GeoJSON ``FeatureCollection`` dict.

        Keyword arguments are those of :func:`get_feature_url` (``bbox``,
        ``cql_filter``, ``max_features``, ``property_names``, ...).
        """
        body = self._request("GET", self.get_feature_url(typename, **query))
        try:
            data = json.loads(body)
        except ValueError as exc:
            raise WFSError(
                f"GetFeature did not return JSON (does the server support outputFormat=application/json?): "
                f"{body[:200].decode('utf-8', errors='replace')}"
            ) from exc
        if not isinstance(data, dict) or data.get("type") != "FeatureCollection":
            raise WFSError("GetFeature JSON is not a FeatureCollection")
        return data

    # --------------------------------------------------------------- writes
    def _write_srs(self) -> tuple[str, bool]:
        srs_name = self.srs_name or ("EPSG:4326" if self.version == "1.0.0" else "urn:ogc:def:crs:EPSG::4326")
        if self.axis_order == "xy":
            swap = False
        elif self.axis_order == "yx":
            swap = True
        else:
            lowered = srs_name.lower()
            swap = not (re.fullmatch(r"epsg:\d+", lowered) or "epsg.xml#" in lowered)
        return srs_name, swap

    def build_transaction(
        self,
        typename: str,
        *,
        inserts: Sequence[Mapping[str, Any]] = (),
        updates: Sequence[UpdateSpec] = (),
        deletes: Sequence[str] = (),
    ) -> bytes:
        """Return the ``Transaction`` XML that :meth:`transaction` would POST (for inspection/debugging)."""
        info = self.describe_feature_type(typename)
        srs_name, swap = self._write_srs()
        return build_transaction_xml(
            info, version=self.version, inserts=inserts, updates=updates, deletes=deletes,
            srs_name=srs_name, swap_axes=swap,
        )

    def transaction(
        self,
        typename: str,
        *,
        inserts: Sequence[Mapping[str, Any]] = (),
        updates: Sequence[UpdateSpec] = (),
        deletes: Sequence[str] = (),
    ) -> TransactionResult:
        """POST one WFS-T ``Transaction`` with the given Insert/Update/Delete operations.

        Parameters
        ----------
        inserts
            GeoJSON Feature dicts (``geometry`` in lon/lat + ``properties``).
        updates
            ``(feature_id, {"geometry": geom | None, "properties": {...}})`` pairs.
        deletes
            Feature ids to remove.
        """
        if not inserts and not updates and not deletes:
            return TransactionResult()
        xml = self.build_transaction(typename, inserts=inserts, updates=updates, deletes=deletes)
        body = self._request("POST", self.url, data=xml, content_type="text/xml; charset=UTF-8")
        return parse_transaction_response(body, version=self.version)

    def insert(self, typename: str, features: Sequence[Mapping[str, Any]] | Mapping[str, Any]) -> TransactionResult:
        """Insert one Feature dict or a sequence/FeatureCollection of them."""
        if isinstance(features, Mapping):
            feats = list(features.get("features", [])) if features.get("type") == "FeatureCollection" else [features]
        else:
            feats = list(features)
        return self.transaction(typename, inserts=feats)

    def update(
        self,
        typename: str,
        feature_id: str,
        *,
        geometry: Mapping[str, Any] | None = None,
        properties: Mapping[str, Any] | None = None,
    ) -> TransactionResult:
        """Update a feature's geometry and/or attributes by id."""
        return self.transaction(typename, updates=[(feature_id, {"geometry": geometry, "properties": properties or {}})])

    def delete(self, typename: str, feature_ids: Sequence[str] | str) -> TransactionResult:
        """Delete features by id."""
        ids = [feature_ids] if isinstance(feature_ids, str) else list(feature_ids)
        return self.transaction(typename, deletes=ids)


# ---------------------------------------------------------------- parsing
def parse_describe_feature_type(body: bytes, typename: str) -> FeatureTypeInfo:
    """Extract namespace/geometry/property info from a ``DescribeFeatureType`` XSD."""
    root = parse_xml(body)
    if root is None:
        raise WFSError("DescribeFeatureType did not return XML")
    err = exception_from_report(root)
    if err is not None:
        raise err

    prefix, _, local = typename.rpartition(":")
    namespace = root.get("targetNamespace", "")
    if not prefix:
        for m in _XMLNS_RE.finditer(body):
            if m.group(2).decode() == namespace and m.group(1).decode() not in ("xsd", "xs", "gml", "wfs"):
                prefix = m.group(1).decode()
                break
        prefix = prefix or "feature"

    element = None
    for el in root:
        if local_name(el.tag) == "element" and el.get("name") == local:
            element = el
            break
    if element is None:
        raise WFSError(f"DescribeFeatureType response does not declare element {local!r} for {typename}")

    complex_type = child_local(element, "complexType")
    if complex_type is None:
        type_ref = (element.get("type") or "").rpartition(":")[2]
        for ct in iter_local(root, "complexType"):
            if ct.get("name") == type_ref:
                complex_type = ct
                break
    if complex_type is None:
        raise WFSError(f"Cannot resolve complexType for {typename}")

    geometry_name: str | None = None
    geometry_type: str | None = None
    properties: dict[str, str] = {}
    for prop in iter_local(complex_type, "element"):
        name = prop.get("name")
        if not name:
            continue
        type_name = prop.get("type") or "xsd:anyType"
        tprefix, _, tlocal = type_name.rpartition(":")
        if tprefix == "gml" and tlocal.endswith("PropertyType"):
            if geometry_name is None:
                geometry_name = name
                geometry_type = normalize_gml_type(tlocal)
            continue
        properties[name] = type_name

    return FeatureTypeInfo(
        typename=typename,
        prefix=prefix,
        local_name=local,
        namespace=namespace,
        geometry_name=geometry_name,
        geometry_type=geometry_type,
        properties=properties,
    )
