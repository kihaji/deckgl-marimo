"""OGC WFS read / WFS-T write support for deckgl-marimo.

* :class:`WFSLayer` — render a feature type as GeoJSON fetched by the browser.
* :class:`WFSClient` — GetCapabilities / DescribeFeatureType / GetFeature and
  WFS-T ``Transaction`` (insert/update/delete) from the Python kernel.
* :class:`WFSEditor` — edit a feature type with the map's drawing tools and
  commit the diff as one transaction.

``WFSClient`` needs ``requests`` (``pip install 'deckgl-marimo[wfs]'``);
``WFSLayer`` and :func:`get_feature_url` have no extra dependencies.
"""

from deckgl_marimo.wfs._client import Capabilities, WFSClient, parse_describe_feature_type
from deckgl_marimo.wfs._editor import ChangeSet, WFSEditor, diff_features
from deckgl_marimo.wfs._errors import WFSError
from deckgl_marimo.wfs._gml import geometry_to_gml
from deckgl_marimo.wfs._layer import WFSLayer
from deckgl_marimo.wfs._transaction import (
    FeatureTypeInfo,
    TransactionResult,
    build_transaction_xml,
    parse_transaction_response,
)
from deckgl_marimo.wfs._url import get_feature_url

__all__ = [
    "WFSLayer",
    "WFSClient",
    "WFSEditor",
    "WFSError",
    "Capabilities",
    "FeatureTypeInfo",
    "TransactionResult",
    "ChangeSet",
    "get_feature_url",
    "geometry_to_gml",
    "build_transaction_xml",
    "parse_transaction_response",
    "parse_describe_feature_type",
    "diff_features",
]
