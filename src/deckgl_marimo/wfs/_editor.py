"""``WFSEditor`` — edit a WFS feature type with the map's drawing tools and commit via WFS-T.

The editor loads features into the widget's editable drawing layer
(``Map.drawing_features``), keeps a pristine snapshot, diffs the current
collection against it, and sends one ``Transaction`` per :meth:`commit`.
Any object with ``get_features(typename, **query)`` and
``transaction(typename, *, inserts, updates, deletes)`` can act as the
client (duck-typed), so other feature stores can be plugged in later.
"""

from __future__ import annotations

import copy
import json
import re
import warnings
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from deckgl_marimo._drawing import EMPTY_FEATURE_COLLECTION, DrawingConfig, DrawingStyle
from deckgl_marimo.wfs._transaction import TransactionResult

if TYPE_CHECKING:
    from deckgl_marimo._map import Map

_PRECISION = 9
_PLACEHOLDER_ID = re.compile(r"^new\d+$")


@dataclass
class ChangeSet:
    """Pending edits relative to the last loaded/committed state."""

    inserts: list[dict[str, Any]] = field(default_factory=list)
    updates: list[tuple[str, dict[str, Any]]] = field(default_factory=list)
    deletes: list[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not (self.inserts or self.updates or self.deletes)

    def summary(self) -> str:
        return f"{len(self.inserts)} insert(s), {len(self.updates)} update(s), {len(self.deletes)} delete(s)"


def _canonical_geometry(geom: Any) -> str:
    def rnd(x: Any) -> Any:
        if isinstance(x, dict):
            return {k: rnd(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)):
            return [rnd(v) for v in x]
        if isinstance(x, float):
            return round(x, _PRECISION)
        return x

    return json.dumps(rnd(geom), sort_keys=True, separators=(",", ":"))


def diff_features(snapshot: Mapping[str, Any], current: Mapping[str, Any]) -> ChangeSet:
    """Diff two FeatureCollections by feature ``id``.

    Features without an id (or with an id unknown to ``snapshot``) are
    inserts; ids missing from ``current`` are deletes; the rest are compared
    by geometry and per-property value and become updates carrying only the
    changed parts (``geometry`` is ``None`` when unchanged).
    """
    snap: dict[str, dict[str, Any]] = {}
    for f in snapshot.get("features", []) or []:
        fid = f.get("id")
        if fid is not None:
            snap[str(fid)] = f

    changes = ChangeSet()
    seen: set[str] = set()
    for f in current.get("features", []) or []:
        fid = f.get("id")
        if fid is None or str(fid) not in snap:
            changes.inserts.append(f)
            continue
        fid = str(fid)
        seen.add(fid)
        old = snap[fid]
        geom_changed = _canonical_geometry(f.get("geometry")) != _canonical_geometry(old.get("geometry"))
        old_props = old.get("properties") or {}
        new_props = f.get("properties") or {}
        changed_props = {k: v for k, v in new_props.items() if old_props.get(k) != v}
        if geom_changed or changed_props:
            changes.updates.append((fid, {"geometry": f.get("geometry") if geom_changed else None, "properties": changed_props}))
    changes.deletes = [fid for fid in snap if fid not in seen]
    return changes


class WFSEditor:
    """Edit features of one WFS feature type on a :class:`~deckgl_marimo.Map`.

    Parameters
    ----------
    map
        The ``Map`` whose drawing layer hosts the editable features.
    client
        A :class:`WFSClient` (or duck-typed equivalent).
    typename
        Feature type to edit.
    bbox, cql_filter
        Default query used by :meth:`load` (``bbox`` accepts ``Map.bounds``).
    max_features
        Cap for :meth:`load` — every synced edit re-sends the whole collection
        through the widget, so keep this modest (a warning is issued when the
        cap is hit).
    style
        :class:`~deckgl_marimo.DrawingStyle` applied by :meth:`set_mode`.

    Workflow
    --------
    ::

        editor = WFSEditor(m, client, "topp:tasmania_roads", bbox=m.bounds)
        editor.load()                   # features -> drawing layer
        editor.set_mode("modify")       # or draw_*, translate, delete
        ...                             # user edits in the browser
        editor.changes().summary()      # "0 insert(s), 2 update(s), 1 delete(s)"
        editor.commit()                 # one WFS-T Transaction, then reload

    In marimo, read ``widget.value["drawing_event"]`` in the cell that calls
    :meth:`changes` so it re-runs after each edit.
    """

    def __init__(
        self,
        map: Map,
        client: Any,
        typename: str,
        *,
        bbox: Any = None,
        cql_filter: str | None = None,
        max_features: int = 1000,
        style: DrawingStyle | None = None,
    ) -> None:
        self.map = map
        self.client = client
        self.typename = typename
        self.bbox = bbox
        self.cql_filter = cql_filter
        self.max_features = max_features
        self.style = style
        self.mode = "view"
        self._snapshot: dict[str, Any] = copy.deepcopy(EMPTY_FEATURE_COLLECTION)
        self._loaded = False

    # ------------------------------------------------------------ loading
    def load(self, *, bbox: Any = None, cql_filter: str | None = None) -> int:
        """Fetch features (GetFeature) into the drawing layer; returns the count.

        ``bbox``/``cql_filter`` override the editor defaults for this and
        subsequent loads.
        """
        if bbox is not None:
            self.bbox = bbox
        if cql_filter is not None:
            self.cql_filter = cql_filter
        query: dict[str, Any] = {"max_features": self.max_features, "srs": "EPSG:4326"}
        if self.bbox is not None:
            query["bbox"] = self.bbox
        if self.cql_filter:
            query["cql_filter"] = self.cql_filter
        fc = self.client.get_features(self.typename, **query)
        features = list(fc.get("features", []) or [])
        if len(features) >= self.max_features:
            warnings.warn(
                f"WFSEditor.load() hit max_features={self.max_features}; the layer may be truncated. "
                "Narrow the bbox/cql_filter or raise max_features.",
                stacklevel=2,
            )
        collection = {"type": "FeatureCollection", "features": features}
        self._snapshot = copy.deepcopy(collection)
        self.map.drawing_features = copy.deepcopy(collection)
        self._loaded = True
        return len(features)

    # ------------------------------------------------------------- state
    @property
    def features(self) -> dict[str, Any]:
        """Current (possibly edited) FeatureCollection in the drawing layer."""
        return self.map.drawing_features or copy.deepcopy(EMPTY_FEATURE_COLLECTION)

    @property
    def snapshot(self) -> dict[str, Any]:
        """Pristine collection as of the last :meth:`load`/:meth:`commit`."""
        return self._snapshot

    def index_of(self, feature_id: str) -> int | None:
        """Position of ``feature_id`` in the drawing layer (for selection), or ``None``."""
        for i, f in enumerate(self.features.get("features", [])):
            if str(f.get("id")) == str(feature_id):
                return i
        return None

    def changes(self) -> ChangeSet:
        """Diff the drawing layer against the snapshot."""
        return diff_features(self._snapshot, self.features)

    # ------------------------------------------------------------- modes
    def set_mode(self, mode: str, *, selected: Sequence[int | str] | None = None) -> None:
        """Switch the drawing mode (``draw_polygon``, ``modify``, ``translate``, ``delete``, ``view`` ...).

        ``selected`` takes feature indexes or ids (for ``modify``/``translate``).
        """
        indexes: list[int] = []
        for item in selected or []:
            if isinstance(item, int):
                indexes.append(item)
            else:
                idx = self.index_of(item)
                if idx is not None:
                    indexes.append(idx)
        self.mode = mode
        self.map.drawing_config = DrawingConfig(mode, selected_feature_indexes=indexes, style=self.style).to_dict()

    def delete_selected(self) -> None:
        """Delete the currently selected feature(s) in the drawing layer."""
        current = self.map.drawing_config or {}
        cfg = DrawingConfig(
            self.mode,
            selected_feature_indexes=list(current.get("selectedFeatureIndexes", [])),
            style=self.style,
            delete_selected=True,
        )
        self.map.drawing_config = cfg.to_dict()

    def update_properties(self, feature: str | int, properties: Mapping[str, Any]) -> None:
        """Set attribute values on a feature (by id or index) in the drawing layer."""
        fc = copy.deepcopy(self.features)
        feats = fc.get("features", [])
        idx = feature if isinstance(feature, int) else self.index_of(feature)
        if idx is None or not (0 <= idx < len(feats)):
            raise KeyError(f"No feature {feature!r} in the drawing layer")
        props = dict(feats[idx].get("properties") or {})
        props.update(properties)
        feats[idx]["properties"] = props
        self.map.drawing_features = fc

    # ------------------------------------------------------------ commit
    def commit(self, *, reload: bool = True) -> TransactionResult:
        """Send pending changes as one WFS-T Transaction.

        With ``reload=True`` (default) the collection is re-fetched afterwards
        so server-assigned ids and values become the new snapshot. With
        ``reload=False`` the returned ``inserted_ids`` are stamped onto the
        inserted features locally instead.
        """
        cs = self.changes()
        if cs.is_empty():
            return TransactionResult()
        result: TransactionResult = self.client.transaction(
            self.typename, inserts=cs.inserts, updates=cs.updates, deletes=cs.deletes,
        )
        if reload:
            self.load()
            return result
        new_ids = list(result.inserted_ids)
        if cs.inserts and (len(new_ids) != len(cs.inserts) or any(_PLACEHOLDER_ID.match(i) for i in new_ids)):
            # Some stores (GeoServer shapefiles) report placeholder ids such as
            # "new0" — only a reload yields the real ids.
            self.load()
            return result
        fc = copy.deepcopy(self.features)
        if new_ids:
            # Servers return inserted ids in Insert order, which is the order
            # the id-less features appear in the collection.
            known = {str(f.get("id")) for f in self._snapshot.get("features", []) if f.get("id") is not None}
            k = 0
            for f in fc.get("features", []):
                if (f.get("id") is None or str(f.get("id")) not in known) and k < len(new_ids):
                    f["id"] = new_ids[k]
                    k += 1
        self._snapshot = copy.deepcopy(fc)
        self.map.drawing_features = fc
        return result

    def discard(self) -> None:
        """Throw away pending edits and restore the snapshot in the drawing layer."""
        self.map.drawing_features = copy.deepcopy(self._snapshot)

    def clear(self) -> None:
        """Empty the drawing layer without touching the server (snapshot kept)."""
        self.map.drawing_features = copy.deepcopy(EMPTY_FEATURE_COLLECTION)
