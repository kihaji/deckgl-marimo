"""``WFSLayer`` — a ``GeoJsonLayer`` whose data is a WFS GetFeature URL."""

from __future__ import annotations

import base64
from collections.abc import Sequence
from typing import Any, ClassVar

from deckgl_marimo._base import BaseLayer
from deckgl_marimo.layers._core import GeoJsonLayer
from deckgl_marimo.wfs._client import WFSClient
from deckgl_marimo.wfs._url import get_feature_url

_WFS_KEYS = frozenset({
    "url", "typename", "version", "bbox", "cql_filter", "max_features",
    "srs", "property_names", "sort_by", "start_index",
})


class WFSLayer(GeoJsonLayer):
    """Render a WFS feature type as GeoJSON, fetched by the browser.

    A thin URL builder on top of :class:`~deckgl_marimo.GeoJsonLayer`: the
    ``GetFeature`` request (``outputFormat=application/json``) is composed in
    Python and loaded by deck.gl, so no data passes through the kernel. The
    query parameters are attributes and can be changed with
    ``Map.update_layer`` — e.g. re-query the visible extent::

        m.update_layer("roads", bbox=m.bounds)

    Because the data is a URL, ``ColorScale`` and callable accessors are not
    available (they need rows in Python). For those, fetch with
    :meth:`WFSClient.get_features` and pass the result to ``GeoJsonLayer``.

    Parameters
    ----------
    url
        WFS endpoint.
    typename
        Feature type (``"topp:states"``).
    version
        WFS version used in the request.
    bbox
        ``(west, south, east, north)`` or ``((west, south), (east, north))``.
    cql_filter
        GeoServer ``CQL_FILTER`` expression.
    max_features
        Cap on returned features.
    srs
        Output CRS; keep ``EPSG:4326`` for deck.gl.
    property_names
        Subset of attributes to return.
    sort_by, start_index
        Ordering / paging.
    **kwargs
        Any ``GeoJsonLayer`` / ``BaseLayer`` parameter, e.g. ``fetch_headers``
        for the browser fetch (tokens travel to the browser; see the
        *Authenticated Data* guide).
    """

    LAYER_TYPE = "GeoJsonLayer"
    _FIELD_KEYS: ClassVar[frozenset[str]] = BaseLayer._FIELD_KEYS | _WFS_KEYS

    def __init__(
        self,
        *,
        url: str,
        typename: str,
        version: str = "2.0.0",
        bbox: Any = None,
        cql_filter: str | None = None,
        max_features: int | None = None,
        srs: str = "EPSG:4326",
        property_names: Sequence[str] | None = None,
        sort_by: str | None = None,
        start_index: int | None = None,
        **kwargs: Any,
    ) -> None:
        # Private state must exist before super().__init__ — BaseLayer.__getattr__
        # proxies unknown attributes to a lazily created Map.
        self._wfs_url = url
        self._wfs_typename = typename
        self._wfs_version = version
        self._wfs_bbox = bbox
        self._wfs_cql_filter = cql_filter
        self._wfs_max_features = max_features
        self._wfs_srs = srs
        self._wfs_property_names = list(property_names) if property_names else None
        self._wfs_sort_by = sort_by
        self._wfs_start_index = start_index
        kwargs.pop("data", None)
        super().__init__(data=self._build_url(), **kwargs)

    @classmethod
    def from_client(cls, client: WFSClient, typename: str, **kwargs: Any) -> WFSLayer:
        """Create a layer using a :class:`WFSClient`'s URL, version and credentials.

        Basic-auth credentials and custom headers are forwarded as browser
        ``fetch_headers`` (they are therefore visible to the browser).
        """
        headers: dict[str, str] = {**client.headers, **(kwargs.pop("fetch_headers", None) or {})}
        if client.auth is not None and "Authorization" not in headers:
            token = base64.b64encode(f"{client.auth[0]}:{client.auth[1]}".encode()).decode()
            headers["Authorization"] = f"Basic {token}"
        return cls(
            url=client.url, typename=typename, version=client.version,
            fetch_headers=headers or None, **kwargs,
        )

    # ----------------------------------------------------------------- URL
    def _build_url(self) -> str:
        return get_feature_url(
            self._wfs_url,
            self._wfs_typename,
            version=self._wfs_version,
            bbox=self._wfs_bbox,
            cql_filter=self._wfs_cql_filter,
            max_features=self._wfs_max_features,
            start_index=self._wfs_start_index,
            srs=self._wfs_srs,
            property_names=self._wfs_property_names,
            sort_by=self._wfs_sort_by,
        )

    def _refresh(self) -> None:
        self.data = self._build_url()

    @property
    def request_url(self) -> str:
        """The GetFeature URL currently used as ``data``."""
        return self._build_url()

    # ------------------------------------------------ update_layer-able props
    @property
    def url(self) -> str:
        return self._wfs_url

    @url.setter
    def url(self, value: str) -> None:
        self._wfs_url = value
        self._refresh()

    @property
    def typename(self) -> str:
        return self._wfs_typename

    @typename.setter
    def typename(self, value: str) -> None:
        self._wfs_typename = value
        self._refresh()

    @property
    def version(self) -> str:
        return self._wfs_version

    @version.setter
    def version(self, value: str) -> None:
        self._wfs_version = value
        self._refresh()

    @property
    def bbox(self) -> Any:
        return self._wfs_bbox

    @bbox.setter
    def bbox(self, value: Any) -> None:
        self._wfs_bbox = value
        self._refresh()

    @property
    def cql_filter(self) -> str | None:
        return self._wfs_cql_filter

    @cql_filter.setter
    def cql_filter(self, value: str | None) -> None:
        self._wfs_cql_filter = value
        self._refresh()

    @property
    def max_features(self) -> int | None:
        return self._wfs_max_features

    @max_features.setter
    def max_features(self, value: int | None) -> None:
        self._wfs_max_features = value
        self._refresh()

    @property
    def srs(self) -> str:
        return self._wfs_srs

    @srs.setter
    def srs(self, value: str) -> None:
        self._wfs_srs = value
        self._refresh()

    @property
    def property_names(self) -> list[str] | None:
        return self._wfs_property_names

    @property_names.setter
    def property_names(self, value: Sequence[str] | None) -> None:
        self._wfs_property_names = list(value) if value else None
        self._refresh()

    @property
    def sort_by(self) -> str | None:
        return self._wfs_sort_by

    @sort_by.setter
    def sort_by(self, value: str | None) -> None:
        self._wfs_sort_by = value
        self._refresh()

    @property
    def start_index(self) -> int | None:
        return self._wfs_start_index

    @start_index.setter
    def start_index(self, value: int | None) -> None:
        self._wfs_start_index = value
        self._refresh()
