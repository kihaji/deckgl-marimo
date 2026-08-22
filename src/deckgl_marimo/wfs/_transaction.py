"""WFS-T ``Transaction`` request builder and response parser (pure; no network)."""

from __future__ import annotations

import datetime as _dt
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any
from xml.sax.saxutils import escape, quoteattr

from deckgl_marimo.wfs._errors import WFSError
from deckgl_marimo.wfs._gml import geometry_to_gml
from deckgl_marimo.wfs._xml import (
    child_local,
    exception_from_report,
    first_local,
    iter_local,
    local_name,
    parse_xml,
)

_NS = {
    "1.0.0": {
        "wfs": "http://www.opengis.net/wfs",
        "ogc": "http://www.opengis.net/ogc",
        "gml": "http://www.opengis.net/gml",
    },
    "1.1.0": {
        "wfs": "http://www.opengis.net/wfs",
        "ogc": "http://www.opengis.net/ogc",
        "gml": "http://www.opengis.net/gml",
    },
    "2.0.0": {
        "wfs": "http://www.opengis.net/wfs/2.0",
        "fes": "http://www.opengis.net/fes/2.0",
        "gml": "http://www.opengis.net/gml/3.2",
    },
}

UpdateSpec = tuple[str, Mapping[str, Any]]
"""``(feature_id, {"geometry": <GeoJSON geometry> | None, "properties": {name: value}})``."""


@dataclass(frozen=True)
class FeatureTypeInfo:
    """What a WFS-T client needs to know about a feature type (from DescribeFeatureType).

    Attributes
    ----------
    typename
        Qualified name as used in requests (``"topp:tasmania_roads"``).
    prefix, local_name, namespace
        XML namespace binding of the feature element.
    geometry_name
        Name of the geometry property (``"the_geom"``); ``None`` for
        geometry-less types.
    geometry_type
        GeoJSON-style declared type (``"MultiLineString"``, ``"Point"``,
        ``"Geometry"`` when unconstrained).
    properties
        Non-geometry attribute names -> XSD type names (``"xsd:string"``).
    """

    typename: str
    prefix: str
    local_name: str
    namespace: str
    geometry_name: str | None
    geometry_type: str | None
    properties: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class TransactionResult:
    """Outcome of a ``Transaction`` request.

    ``inserted_ids`` are the server-assigned ids in Insert order (use them to
    re-identify freshly created features). For WFS 1.0.0 the server reports
    no update/delete totals, so those are ``0`` on success.
    """

    inserted: int = 0
    updated: int = 0
    deleted: int = 0
    inserted_ids: list[str] = field(default_factory=list)
    raw: str = ""

    @property
    def total(self) -> int:
        return self.inserted + self.updated + self.deleted


def _value_text(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (_dt.datetime, _dt.date)):
        return value.isoformat()
    return str(value)


def _is_schema_property(name: str, info: FeatureTypeInfo) -> bool:
    # Without a schema (empty properties) we cannot filter; send everything.
    return not info.properties or name in info.properties


def build_transaction_xml(
    info: FeatureTypeInfo,
    *,
    version: str = "2.0.0",
    inserts: Sequence[Mapping[str, Any]] = (),
    updates: Sequence[UpdateSpec] = (),
    deletes: Sequence[str] = (),
    srs_name: str = "urn:ogc:def:crs:EPSG::4326",
    swap_axes: bool = True,
) -> bytes:
    """Serialize Insert/Update/Delete operations into one ``wfs:Transaction``.

    Insert features are GeoJSON Feature dicts (``geometry`` + ``properties``);
    properties not declared by the schema are skipped (editable-layer
    bookkeeping such as ``shape``/``editProperties`` never reaches the
    server). Update properties set to ``None`` are sent as empty values.
    """
    if version not in _NS:
        raise ValueError(f"Unsupported WFS version {version!r}")
    ns = _NS[version]
    filt = "fes" if version == "2.0.0" else "ogc"
    p = info.prefix

    def gml(geom: Mapping[str, Any]) -> str:
        return geometry_to_gml(
            dict(geom), version=version, srs_name=srs_name, swap_axes=swap_axes,
            target_type=info.geometry_type,
        )

    def id_filter(fid: str) -> str:
        if filt == "fes":
            return f"<fes:Filter><fes:ResourceId rid={quoteattr(str(fid))}/></fes:Filter>"
        return f"<ogc:Filter><ogc:FeatureId fid={quoteattr(str(fid))}/></ogc:Filter>"

    def prop(name: str, value: str, is_xml: bool) -> str:
        ref = "ValueReference" if version == "2.0.0" else "Name"
        val = value if is_xml else escape(value)
        return f"<wfs:Property><wfs:{ref}>{escape(name)}</wfs:{ref}><wfs:Value>{val}</wfs:Value></wfs:Property>"

    parts: list[str] = []
    for feature in inserts:
        geom = feature.get("geometry")
        props = feature.get("properties") or {}
        body = ""
        if geom is not None:
            if not info.geometry_name:
                raise WFSError(f"{info.typename} has no geometry property; cannot insert a geometry")
            body += f"<{p}:{info.geometry_name}>{gml(geom)}</{p}:{info.geometry_name}>"
        for name, value in props.items():
            if value is None or not _is_schema_property(name, info) or name == info.geometry_name:
                continue
            body += f"<{p}:{name}>{escape(_value_text(value))}</{p}:{name}>"
        parts.append(f"<wfs:Insert><{p}:{info.local_name}>{body}</{p}:{info.local_name}></wfs:Insert>")

    for fid, change in updates:
        props_xml = ""
        geom = change.get("geometry")
        if geom is not None:
            if not info.geometry_name:
                raise WFSError(f"{info.typename} has no geometry property; cannot update a geometry")
            props_xml += prop(info.geometry_name, gml(geom), True)
        for name, value in (change.get("properties") or {}).items():
            if not _is_schema_property(name, info) or name == info.geometry_name:
                continue
            props_xml += prop(name, "" if value is None else _value_text(value), False)
        if not props_xml:
            raise WFSError(
                f"Update of {fid!r} has nothing to apply: no geometry and no properties declared by "
                f"{info.typename} (known: {sorted(info.properties)})"
            )
        parts.append(f'<wfs:Update typeName="{p}:{info.local_name}">{props_xml}{id_filter(fid)}</wfs:Update>')

    for fid in deletes:
        parts.append(f'<wfs:Delete typeName="{p}:{info.local_name}">{id_filter(fid)}</wfs:Delete>')

    xmlns = " ".join(f'xmlns:{k}="{v}"' for k, v in ns.items())
    xmlns += f' xmlns:{p}="{info.namespace}"' if info.namespace else ""
    doc = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<wfs:Transaction service="WFS" version="{version}" {xmlns}>'
        + "".join(parts)
        + "</wfs:Transaction>"
    )
    return doc.encode("utf-8")


def _int_text(elem: Any) -> int:
    try:
        return int((elem.text or "0").strip()) if elem is not None else 0
    except ValueError:
        return 0


def parse_transaction_response(body: bytes, *, version: str = "2.0.0", status: int | None = None) -> TransactionResult:
    """Parse a ``TransactionResponse`` (1.1/2.0) or ``WFS_TransactionResponse`` (1.0).

    Raises :class:`WFSError` for OWS exception reports, 1.0 ``FAILED``
    status, or unparseable bodies.
    """
    root = parse_xml(body)
    raw = body.decode("utf-8", errors="replace")
    if root is None:
        raise WFSError(f"Transaction returned a non-XML response (HTTP {status}): {raw[:300]}", status=status)
    err = exception_from_report(root, status=status)
    if err is not None:
        raise err

    ids: list[str] = []
    for container_name in ("InsertResults", "InsertResult"):
        for container in iter_local(root, container_name):
            for elem in container.iter():
                lname = local_name(elem.tag)
                value = elem.get("fid") if lname == "FeatureId" else elem.get("rid") if lname == "ResourceId" else None
                # GeoServer emits fid="none" in InsertResults of update/delete-only transactions.
                if value and value != "none":
                    ids.append(str(value))

    summary = first_local(root, "TransactionSummary")
    if summary is not None:
        inserted = _int_text(child_local(summary, "totalInserted"))
        if inserted == 0:
            ids = []
        return TransactionResult(
            inserted=inserted,
            updated=_int_text(child_local(summary, "totalUpdated")),
            deleted=_int_text(child_local(summary, "totalDeleted")),
            inserted_ids=ids,
            raw=raw,
        )

    # WFS 1.0.0: <wfs:TransactionResult><wfs:Status><wfs:SUCCESS/></wfs:Status><wfs:Message>...
    result = first_local(root, "TransactionResult")
    if result is not None:
        status_el = first_local(result, "Status")
        state = local_name(status_el[0].tag) if status_el is not None and len(status_el) else "SUCCESS"
        if state != "SUCCESS":
            msg_el = first_local(result, "Message")
            message = (msg_el.text or "").strip() if msg_el is not None else ""
            raise WFSError(f"Transaction {state}: {message or raw[:300]}", status=status, code=state)
        return TransactionResult(inserted=len(ids), inserted_ids=ids, raw=raw)

    raise WFSError(f"Unrecognised transaction response: {raw[:300]}", status=status)
