# Troubleshooting

## Map flashes black / camera resets when a slider moves

The `Map` widget is being recreated on every reactive run. Create the
`Map` in a cell with **no** slider dependencies and update layers from a
separate cell with `deck_map.set_layers([...])` — see
[Reactive Patterns](guides/reactive-patterns.md).

## Binary layers stop rendering after a reactive update

You are assigning `deck_map.layer_specs` directly, which skips binary
re-packing. Use `deck_map.set_layers([...])` instead — it re-serializes
specs *and* binary buffers together.

## `Content-Length` errors in the marimo console

Fixed in marimo ≥ 0.22.0 — update marimo.

## Blank map / WebGL errors (WSL, remote desktops, headless)

deck.gl requires WebGL2. In WSL, make sure your browser has hardware
acceleration enabled (check `chrome://gpu`, or test at
[webglreport.com](https://webglreport.com)). For headless Chromium
testing, launch with
`--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader`.

## `ImportError` from `as_widget()`

marimo is an optional dependency. Inside a marimo notebook it is present
by definition; elsewhere install `deckgl-marimo[marimo]` or use the `Map`
widget directly.

## `Unknown property` TypeError when constructing a layer

Layer kwargs are validated against the layer's declared parameters to
catch typos — the error lists closest matches. To pass an undocumented
deck.gl prop through deliberately, add `_unsafe_props=True`.

## Building from source fails asking for Node

Wheels from PyPI are prebuilt. Installing from a git checkout or sdist
compiles the JS bundle and needs Node.js 20+ on PATH (see
[Installation](getting-started/installation.md)).
