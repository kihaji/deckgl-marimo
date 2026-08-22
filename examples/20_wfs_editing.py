# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "deckgl-marimo[wfs]",
# ]
#
# [tool.uv.sources]
# deckgl-marimo = { path = ".." }
# ///
"""Edit a WFS feature type with the drawing tools and commit via WFS-T.

Needs a transactional WFS. The defaults target the GeoServer docker image
and its sample data (`topp:tasmania_roads`, a writable shapefile):

    docker run -d --name geoserver -p 8080:8080 docker.osgeo.org/geoserver:2.27.1

Override with the WFS_URL / WFS_AUTH (user:password) / WFS_TYPENAME
environment variables.
"""

import marimo

__generated_with = "0.22.0"
app = marimo.App(width="full")


@app.cell
def _():
    import os

    import marimo as mo

    import deckgl_marimo as dgl
    from deckgl_marimo.wfs import WFSClient, WFSEditor, WFSError

    return WFSClient, WFSEditor, WFSError, dgl, mo, os


@app.cell
def _(WFSClient, os):
    WFS_URL = os.environ.get("WFS_URL", "http://localhost:8080/geoserver/wfs")
    TYPENAME = os.environ.get("WFS_TYPENAME", "topp:tasmania_roads")
    user, _, password = os.environ.get("WFS_AUTH", "admin:geoserver").partition(":")
    wfs = WFSClient(WFS_URL, auth=(user, password))
    return TYPENAME, wfs


@app.cell
def _(TYPENAME, WFSEditor, dgl, wfs):
    # Stable Map cell. The editor seeds the drawing layer from the WFS.
    deck_map = dgl.Map(basemap="positron", center=(146.8, -41.6), zoom=7)
    widget = deck_map.as_widget()
    editor = WFSEditor(
        deck_map,
        wfs,
        TYPENAME,
        max_features=500,
        style=dgl.DrawingStyle(line_color="#d7301f", line_width=3, edit_handle_point_color="#222222"),
    )
    return deck_map, editor, widget


@app.cell
def _(WFSError, editor, mo):
    try:
        n = editor.load()
        status = mo.md(f"Loaded **{n}** features from `{editor.typename}`.")
    except WFSError as exc:
        status = mo.callout(mo.md(f"Could not load features: `{exc}`\n\nIs GeoServer running on port 8080?"), kind="danger")
    status
    return


@app.cell
def _(mo):
    mode = mo.ui.radio(
        options=["view", "modify", "translate", "draw_line", "delete"],
        value="modify",
        label="Mode",
        inline=True,
    )
    mode
    return (mode,)


@app.cell
def _(editor, mode):
    editor.set_mode(mode.value)
    return


@app.cell
def _(widget):
    widget
    return


@app.cell
def _(mo):
    commit = mo.ui.run_button(label="Commit to WFS", kind="success")
    discard = mo.ui.run_button(label="Discard edits", kind="warn")
    mo.hstack([commit, discard])
    return commit, discard


@app.cell
def _(WFSError, commit, discard, editor, mo):
    # Runs when either button is pressed.
    result_md = ""
    if commit.value:
        try:
            result = editor.commit()
            result_md = f"Committed: {result.inserted} inserted, {result.updated} updated, {result.deleted} deleted."
        except WFSError as exc:
            result_md = f"Transaction failed: `{exc}`"
    elif discard.value:
        editor.discard()
        result_md = "Edits discarded."
    mo.md(result_md) if result_md else None
    return


@app.cell
def _(editor, mo, widget):
    # Depend on drawing_event so this re-runs after every edit.
    _event = widget.value.get("drawing_event") or {}
    changes = editor.changes()
    lines = [f"**Pending:** {changes.summary()}  (last event: `{_event.get('type', '—')}`)"]
    lines += [f"- update `{fid}`: " + ("geometry " if c["geometry"] else "") + f"{c['properties'] or ''}" for fid, c in changes.updates]
    lines += [f"- delete `{fid}`" for fid in changes.deletes]
    lines += [f"- insert ({f['geometry']['type']})" for f in changes.inserts]
    mo.md("\n".join(lines))
    return


if __name__ == "__main__":
    app.run()
