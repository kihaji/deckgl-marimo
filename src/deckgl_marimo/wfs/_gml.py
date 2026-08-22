"""GeoJSON geometry -> GML text, for WFS-T ``Insert``/``Update`` bodies.

Three dialects, selected by WFS version:

* ``1.0.0`` -> GML 2 (``gml:coordinates``, ``outerBoundaryIs``)
* ``1.1.0`` -> GML 3.1.1 (``gml:pos``/``gml:posList``, ``exterior``)
* ``2.0.0`` -> GML 3.2 (as 3.1.1 plus a ``gml:id`` on every geometry)

Only the first two coordinate dimensions are encoded. Axis swapping
(``swap_axes=True``) writes ``lat lon`` for servers that apply EPSG axis
order to ``urn:ogc:def:crs:EPSG::4326`` (GeoServer does).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any
from uuid import uuid4

from deckgl_marimo.wfs._errors import WFSError

GEOMETRY_TYPES = (
    "Point", "LineString", "Polygon",
    "MultiPoint", "MultiLineString", "MultiPolygon", "GeometryCollection",
)

_SINGLE_TO_MULTI = {
    "Point": "MultiPoint",
    "LineString": "MultiLineString",
    "Polygon": "MultiPolygon",
}

# Normalise GML property-type names from DescribeFeatureType to GeoJSON types.
_GML_TYPE_ALIASES = {
    "MultiSurface": "MultiPolygon",
    "MultiCurve": "MultiLineString",
    "Surface": "Polygon",
    "Curve": "LineString",
    "MultiGeometry": "GeometryCollection",
}


def normalize_gml_type(gml_type: str) -> str:
    """``"MultiSurfacePropertyType"`` / ``"gml:PointPropertyType"`` -> GeoJSON-ish type name."""
    name = gml_type.split(":", 1)[-1]
    if name.endswith("PropertyType"):
        name = name[: -len("PropertyType")]
    return _GML_TYPE_ALIASES.get(name, name)


def _fmt(value: Any) -> str:
    text = format(float(value), ".12f").rstrip("0").rstrip(".")
    return "0" if text in ("", "-0") else text


def _pair(coord: Iterable[Any], swap: bool) -> tuple[str, str]:
    c = list(coord)
    if len(c) < 2:
        raise WFSError(f"Coordinate must have at least 2 dimensions, got {c!r}")
    x, y = _fmt(c[0]), _fmt(c[1])
    return (y, x) if swap else (x, y)


def promote_geometry(geom: dict[str, Any], target_type: str | None) -> dict[str, Any]:
    """Wrap a single geometry into the Multi* type the schema declares.

    ``target_type`` is a GeoJSON type name or ``"Geometry"``/``None`` (no
    constraint). Mismatches that cannot be promoted raise :class:`WFSError`.
    """
    gtype = geom.get("type")
    if gtype not in GEOMETRY_TYPES:
        raise WFSError(f"Unsupported GeoJSON geometry type {gtype!r}")
    if not target_type or target_type in ("Geometry", "GeometryCollection") or target_type == gtype:
        return geom
    if _SINGLE_TO_MULTI.get(gtype) == target_type:
        return {"type": target_type, "coordinates": [geom["coordinates"]]}
    raise WFSError(
        f"Geometry type {gtype!r} does not match the feature type's declared geometry {target_type!r} "
        "(and cannot be promoted)."
    )


class _Encoder:
    def __init__(self, *, version: str, srs_name: str, swap_axes: bool) -> None:
        self.gml2 = version == "1.0.0"
        self.gml_ids = version == "2.0.0"
        self.srs_name = srs_name
        self.swap = swap_axes
        self._prefix = f"g{uuid4().hex[:8]}"
        self._n = 0

    def _attrs(self, outer: bool) -> str:
        parts = []
        if self.gml_ids:
            self._n += 1
            parts.append(f' gml:id="{self._prefix}.{self._n}"')
        if outer:
            parts.append(f' srsName="{self.srs_name}"')
        return "".join(parts)

    # -- coordinate strings -------------------------------------------------
    def _coords2(self, coords: Iterable[Iterable[Any]]) -> str:
        return " ".join(",".join(_pair(c, self.swap)) for c in coords)

    def _poslist(self, coords: Iterable[Iterable[Any]]) -> str:
        return " ".join(" ".join(_pair(c, self.swap)) for c in coords)

    # -- primitives ---------------------------------------------------------
    def point(self, coords: Any, outer: bool) -> str:
        a = self._attrs(outer)
        if self.gml2:
            return f"<gml:Point{a}><gml:coordinates>{','.join(_pair(coords, self.swap))}</gml:coordinates></gml:Point>"
        return f"<gml:Point{a}><gml:pos>{' '.join(_pair(coords, self.swap))}</gml:pos></gml:Point>"

    def linestring(self, coords: Any, outer: bool) -> str:
        a = self._attrs(outer)
        if self.gml2:
            return f"<gml:LineString{a}><gml:coordinates>{self._coords2(coords)}</gml:coordinates></gml:LineString>"
        return f"<gml:LineString{a}><gml:posList>{self._poslist(coords)}</gml:posList></gml:LineString>"

    def _ring(self, coords: Any) -> str:
        a = self._attrs(False)
        if self.gml2:
            return f"<gml:LinearRing{a}><gml:coordinates>{self._coords2(coords)}</gml:coordinates></gml:LinearRing>"
        return f"<gml:LinearRing{a}><gml:posList>{self._poslist(coords)}</gml:posList></gml:LinearRing>"

    def polygon(self, rings: Any, outer: bool) -> str:
        a = self._attrs(outer)
        rings = list(rings)
        if not rings:
            raise WFSError("Polygon must have at least one ring")
        ext, holes = ("outerBoundaryIs", "innerBoundaryIs") if self.gml2 else ("exterior", "interior")
        body = f"<gml:{ext}>{self._ring(rings[0])}</gml:{ext}>"
        body += "".join(f"<gml:{holes}>{self._ring(r)}</gml:{holes}>" for r in rings[1:])
        return f"<gml:Polygon{a}>{body}</gml:Polygon>"

    # -- multis -------------------------------------------------------------
    def multi(self, gtype: str, parts: Any, outer: bool) -> str:
        if self.gml2:
            container, member, fn = {
                "MultiPoint": ("MultiPoint", "pointMember", self.point),
                "MultiLineString": ("MultiLineString", "lineStringMember", self.linestring),
                "MultiPolygon": ("MultiPolygon", "polygonMember", self.polygon),
            }[gtype]
        else:
            container, member, fn = {
                "MultiPoint": ("MultiPoint", "pointMember", self.point),
                "MultiLineString": ("MultiCurve", "curveMember", self.linestring),
                "MultiPolygon": ("MultiSurface", "surfaceMember", self.polygon),
            }[gtype]
        a = self._attrs(outer)
        body = "".join(f"<gml:{member}>{fn(p, False)}</gml:{member}>" for p in parts)
        return f"<gml:{container}{a}>{body}</gml:{container}>"

    def collection(self, geoms: Any, outer: bool) -> str:
        a = self._attrs(outer)
        body = "".join(f"<gml:geometryMember>{self.encode(g, False)}</gml:geometryMember>" for g in geoms)
        return f"<gml:MultiGeometry{a}>{body}</gml:MultiGeometry>"

    def encode(self, geom: dict[str, Any], outer: bool = True) -> str:
        gtype = geom.get("type")
        if gtype == "Point":
            return self.point(geom["coordinates"], outer)
        if gtype == "LineString":
            return self.linestring(geom["coordinates"], outer)
        if gtype == "Polygon":
            return self.polygon(geom["coordinates"], outer)
        if gtype in ("MultiPoint", "MultiLineString", "MultiPolygon"):
            return self.multi(gtype, geom["coordinates"], outer)
        if gtype == "GeometryCollection":
            return self.collection(geom.get("geometries", []), outer)
        raise WFSError(f"Unsupported GeoJSON geometry type {gtype!r}")


def geometry_to_gml(
    geom: dict[str, Any],
    *,
    version: str = "2.0.0",
    srs_name: str = "urn:ogc:def:crs:EPSG::4326",
    swap_axes: bool = True,
    target_type: str | None = None,
) -> str:
    """Encode a GeoJSON geometry as GML for the given WFS ``version``.

    Parameters
    ----------
    geom
        GeoJSON geometry dict (lon/lat order, as GeoJSON mandates).
    version
        WFS version; selects GML 2 / 3.1.1 / 3.2.
    srs_name
        ``srsName`` written on the outermost geometry element.
    swap_axes
        Write ``lat lon`` instead of ``lon lat`` (needed with
        ``urn:ogc:def:crs:EPSG::4326`` on GeoServer).
    target_type
        Declared geometry type of the feature type (from DescribeFeatureType);
        single geometries are promoted to the matching Multi* type.
    """
    geom = promote_geometry(geom, target_type)
    return _Encoder(version=version, srs_name=srs_name, swap_axes=swap_axes).encode(geom)
