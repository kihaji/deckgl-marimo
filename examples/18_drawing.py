# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "deckgl-marimo",
# ]
#
# [tool.uv.sources]
# deckgl-marimo = { path = ".." }
# ///
"""Interactive drawing/editing on the map.

Draw polygons, lines, circles, and points; modify or translate them;
click features to delete them in delete mode. Drawn features arrive in
Python as GeoJSON via the reactive `drawing_features` value.
"""

import marimo

__generated_with = "0.22.0"
app = marimo.App(width="full")


@app.cell
def _():
    import json

    import marimo as mo

    import deckgl_marimo as dgl

    return dgl, json, mo


@app.cell
def _(mo):
    mode = mo.ui.radio(
        options=[
            "view", "draw_polygon", "draw_line", "draw_point",
            "draw_circle", "draw_rectangle", "modify", "translate", "delete",
        ],
        value="draw_polygon",
        label="Mode",
        inline=True,
    )
    mode
    return (mode,)


@app.cell
def _(dgl):
    # Stable Map cell — the drawing config is swapped reactively below.
    deck_map = dgl.Map(basemap="positron", center=(-98.5, 39.8), zoom=4)
    widget = deck_map.as_widget()
    return deck_map, widget


@app.cell
def _(widget):
    widget
    return


@app.cell
def _(deck_map, dgl, mode):
    # Reactive: switch drawing mode from the radio control
    deck_map.drawing_config = dgl.DrawingConfig(
        mode.value,
        style=dgl.DrawingStyle(
            fill_color=[255, 140, 0, 100],
            line_color="#222222",
            line_width=2,
        ),
    ).to_dict()
    return


@app.cell
def _(json, mo, widget):
    features = widget.value.get("drawing_features", {}) or {}
    event = widget.value.get("drawing_event", {}) or {}
    n = len(features.get("features", []))
    mo.md(f"""
**{n} feature(s) drawn** — last event: `{event.get("type", "—")}`

```json
{json.dumps(features, indent=2)[:2000]}
```
""")
    return


@app.cell
def _(deck_map, dgl, mo):
    clear = mo.ui.run_button(label="Clear all features")
    if clear.value:
        deck_map.drawing_features = dict(dgl.EMPTY_FEATURE_COLLECTION)
    clear
    return


if __name__ == "__main__":
    app.run()
