"""Namespace-agnostic XML helpers shared by the WFS modules."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Iterator

from deckgl_marimo.wfs._errors import WFSError


def local_name(tag: str) -> str:
    """``"{http://ns}Name"`` -> ``"Name"``; plain tags pass through."""
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def iter_local(root: ET.Element, name: str) -> Iterator[ET.Element]:
    """Yield every descendant (including ``root``) whose local tag is ``name``."""
    for elem in root.iter():
        if local_name(elem.tag) == name:
            yield elem


def first_local(root: ET.Element, name: str) -> ET.Element | None:
    return next(iter_local(root, name), None)


def child_local(elem: ET.Element, name: str) -> ET.Element | None:
    """Direct child with local tag ``name``."""
    for child in elem:
        if local_name(child.tag) == name:
            return child
    return None


def parse_xml(body: bytes) -> ET.Element | None:
    """Parse ``body`` if it looks like XML; return ``None`` otherwise."""
    stripped = body.lstrip()
    if not stripped.startswith(b"<"):
        return None
    try:
        return ET.fromstring(stripped)
    except ET.ParseError:
        return None


def exception_from_report(root: ET.Element, *, status: int | None = None) -> WFSError | None:
    """Turn an OWS ``ExceptionReport`` / WFS 1.0 ``ServiceExceptionReport`` into a :class:`WFSError`.

    Returns ``None`` when ``root`` is not an exception document.
    """
    name = local_name(root.tag)
    if name == "ExceptionReport":
        exc = first_local(root, "Exception")
        code = exc.get("exceptionCode") if exc is not None else None
        locator = exc.get("locator") if exc is not None else None
        texts = [(t.text or "").strip() for t in iter_local(root, "ExceptionText")]
        message = "; ".join(t for t in texts if t) or "WFS ExceptionReport"
        return WFSError(f"WFS error [{code or 'Exception'}]: {message}", status=status, code=code, locator=locator)
    if name == "ServiceExceptionReport":
        exc = first_local(root, "ServiceException")
        code = exc.get("code") if exc is not None else None
        locator = exc.get("locator") if exc is not None else None
        message = (exc.text or "").strip() if exc is not None else ""
        return WFSError(
            f"WFS error [{code or 'ServiceException'}]: {message or 'ServiceExceptionReport'}",
            status=status, code=code, locator=locator,
        )
    return None
