# WFS & WFS-T Editing

Read features from an OGC **Web Feature Service** and write edits back with
**WFS-T transactions** (insert / update / delete) — all from a marimo
notebook. Everything lives in `deckgl_marimo.wfs`:

| Piece | What it does | Needs |
|-------|--------------|-------|
| `WFSLayer` | A `GeoJsonLayer` whose data is a `GetFeature` URL; the browser fetches the GeoJSON | nothing extra |
| `WFSClient` | GetCapabilities / DescribeFeatureType / GetFeature and `Transaction` from the Python kernel | `pip install 'deckgl-marimo[wfs]'` (`requests`) |
| `WFSEditor` | Edit a feature type with the map's drawing tools and commit the diff as one transaction | `WFSClient` |

Tested against GeoServer (WFS 2.0.0, 1.1.0 and 1.0.0); other servers that
follow the spec should work — see [Server notes](#server-notes).

## Read: `WFSLayer`

```python
import deckgl_marimo as dgl
from deckgl_marimo.wfs import WFSLayer

states = WFSLayer(
    url="https://ahocevar.com/geoserver/wfs",
    typename="topp:states",
    id="states",
    max_features=100,
    get_fill_color=(60, 120, 200, 80),
    get_line_color=(30, 60, 100, 255),
    line_width_min_pixels=1,
    pickable=True,
)
m = dgl.Map(layers=[states], basemap="positron", center=(-96, 38), zoom=3.5)
widget = m.as_widget()
```

`WFSLayer` only builds the request URL
(`SERVICE=WFS&REQUEST=GetFeature&outputFormat=application/json&...`);
deck.gl loads it like any remote GeoJSON, so nothing passes through the
kernel. Query options: `bbox`, `cql_filter` (GeoServer), `max_features`,
`start_index`, `property_names`, `sort_by`, `srs`, `version`.

### Re-query the visible extent

The query parameters are attributes, so `Map.update_layer` rebuilds the
URL — pair it with `m.bounds` (see *Picking & Events*):

```python
# cell: a button keeps this from re-fetching on every pan
refresh = mo.ui.run_button(label="Load features in view")
refresh

# cell
if refresh.value:
    m.update_layer("states", bbox=m.bounds)
```

`bbox` accepts `(west, south, east, north)` or the
`((west, south), (east, north))` shape of `m.bounds`, and is always sent with
an explicit CRS (`BBOX=w,s,e,n,EPSG:4326`) so axis order is unambiguous.

### Styling by attribute

Because the data is a URL, `ColorScale` and callable accessors are not
available on `WFSLayer` (they need the rows in Python). Fetch with the client
instead and use a plain `GeoJsonLayer`:

```python
from deckgl_marimo.wfs import WFSClient

wfs = WFSClient("https://ahocevar.com/geoserver/wfs")
fc = wfs.get_features("topp:states", property_names=["STATE_NAME", "PERSONS", "the_geom"])

layer = dgl.GeoJsonLayer(
    data=fc,
    get_fill_color=dgl.ColorScale("PERSONS", palette="viridis", scale="log"),
)
```

### Authentication

For a protected WFS, either let the browser send credentials
(`WFSLayer(..., fetch_headers={"Authorization": "Bearer ..."})` — see
*Authenticated Data*; the token travels to the browser) or keep them in the
kernel with `WFSClient(url, auth=("user", "pw"))` /
`headers={...}` and pass the fetched GeoJSON to a `GeoJsonLayer`.
`WFSLayer.from_client(client, typename)` copies a client's URL, version and
basic-auth header into a browser-side layer.

## `WFSClient`

```python
wfs = WFSClient("http://localhost:8080/geoserver/wfs", auth=("admin", "geoserver"))

caps = wfs.get_capabilities()
caps.feature_types            # ['topp:tasmania_roads', 'topp:states', ...]
caps.supports_transaction     # True when the server advertises WFS-T

info = wfs.describe_feature_type("topp:tasmania_roads")
info.geometry_name, info.geometry_type, info.properties
# ('the_geom', 'MultiLineString', {'TYPE': 'xsd:string'})

fc = wfs.get_features("topp:tasmania_roads", bbox=m.bounds, max_features=500)

# WFS-T
wfs.insert("topp:tasmania_roads", {"type": "Feature", "geometry": {...}, "properties": {"TYPE": "road"}})
wfs.update("topp:tasmania_roads", "tasmania_roads.3", properties={"TYPE": "highway"})
wfs.delete("topp:tasmania_roads", ["tasmania_roads.7"])
result = wfs.transaction("topp:tasmania_roads", inserts=[...], updates=[...], deletes=[...])
result.inserted, result.updated, result.deleted, result.inserted_ids
```

Geometries are plain GeoJSON (lon/lat). The client encodes them as GML for
the chosen `version` (GML 2 / 3.1.1 / 3.2), promotes single geometries to
the Multi\* type the schema declares (a drawn `LineString` becomes a
`MultiLineString` for `tasmania_roads`), skips properties the schema does
not know, and handles the lat/lon axis order GeoServer expects for
`urn:ogc:def:crs:EPSG::4326`. Errors (HTTP, OWS `ExceptionReport`, a
read-only layer) raise `WFSError` with `.code` / `.locator` when available.

`wfs.build_transaction(...)` returns the XML that would be posted — handy for
debugging against a picky server.

## Edit: `WFSEditor`

`WFSEditor` connects a feature type to the map's drawing layer
(see *Drawing & Editing*):

```python
from deckgl_marimo.wfs import WFSClient, WFSEditor

# stable cells ------------------------------------------------------------
m = dgl.Map(basemap="positron", center=(146.5, -42), zoom=7)
widget = m.as_widget()
wfs = WFSClient("http://localhost:8080/geoserver/wfs", auth=("admin", "geoserver"))
editor = WFSEditor(m, wfs, "topp:tasmania_roads", max_features=500)
editor.load()                    # GetFeature -> m.drawing_features (+ snapshot)

# reactive cell: mode radio -> editor ------------------------------------
editor.set_mode(mode.value)      # "modify", "translate", "draw_line", "delete", "view" ...

# reactive cell: pending changes -----------------------------------------
_ = widget.value.get("drawing_event")   # re-run after every edit
changes = editor.changes()
mo.md(f"Pending: **{changes.summary()}**")

# commit / discard buttons -----------------------------------------------
if commit.value:
    result = editor.commit()     # one Transaction, then reload from the server
if discard.value:
    editor.discard()
```

How it works:

1. `load()` fetches the features (optionally `bbox=`/`cql_filter=`) into the
   editable layer and keeps a snapshot.
2. The user draws, moves vertices, translates or deletes features in the
   browser; `feature.id` and `properties` survive geometry edits.
3. `changes()` diffs the layer against the snapshot **by feature id**:
   id-less features are inserts, missing ids are deletes, changed
   geometry/properties are updates (only the changed parts are sent).
4. `commit()` posts a single `Transaction` and reloads, so server-assigned
   ids become authoritative. `discard()` restores the snapshot.

Attributes are edited from Python —
`editor.update_properties("tasmania_roads.3", {"TYPE": "highway"})` (by id or
index) — e.g. from a `mo.ui.form` bound to the picked feature. `set_mode(mode,
selected=[...])` accepts ids or indexes for `modify`/`translate`, and
`delete_selected()` removes the selection.

!!! note "Overlay mode"
    Editing uses the map's drawing layer, which needs deck.gl's interleaved
    overlay mode; the widget switches to it automatically the first time a
    drawing mode is set (see *Drawing & Editing*), or start with
    `dgl.Map(interleaved=True)`.

!!! note "Keep the collection small"
    Every synced edit re-sends the whole FeatureCollection between browser
    and kernel. Load a few hundred features at a time (`bbox=m.bounds`,
    `cql_filter=`, `max_features=`); `load()` warns when it hits the cap.
    One feature type is editable at a time (the map has a single drawing
    layer) — call `load()` on another editor to switch.

## Server notes

- **GeoServer**: the layer must be writable (data store + *Service Level:
  Transactional* in the WFS settings) and the user needs write access;
  anonymous writes fail with `WFSError: ... is read-only`. Shapefile stores
  report placeholder insert ids (`new0`); `commit()` reloads so you still get
  real ids. Shapefile attribute widths truncate long strings silently.
- **Versions**: `2.0.0` (default, `fes:ResourceId`/GML 3.2), `1.1.0`
  (`ogc:FeatureId`/GML 3.1.1), `1.0.0` (GML 2; no update/delete totals in the
  response). QGIS Server only transacts in 1.0.0.
- **Axis order**: transactions default to `urn:ogc:def:crs:EPSG::4326` with
  lat/lon order (GeoServer's reading of the URN). For servers that expect
  lon/lat, use `WFSClient(..., srs_name="EPSG:4326")` or `axis_order="xy"`.
- **Reads** always request `srsName=EPSG:4326` + GeoJSON, which is lon/lat on
  every server we know of; GeoServer 3-D coordinates pass through unchanged
  (only the first two dimensions are written back).
- `WFSEditor` only needs `get_features()` and `transaction()`, so a client
  for another store (e.g. OGC API – Features Part 4) can be dropped in later.

See `examples/19_wfs.py` (read) and `examples/20_wfs_editing.py` (edit, runs
against a local docker GeoServer).
