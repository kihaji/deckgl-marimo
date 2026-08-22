# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `Map.bounds` — the visible map extent as `((west, south), (east, north))`
  (lower-left, upper-right), reported by the frontend alongside the other
  `viewport` fields (`widget.value["viewport"]["bounds"]`). Same shape
  `fit_bounds()` takes, so views round-trip.

### Changed
- The `viewport` readback is now published as soon as the map has loaded,
  not only after the first user interaction.
- Kernel-side perf watchdog (`tests/perf_watchdog/`, opt-in via
  `make test-perf` / `pytest --run-perf`; not run in CI) guarding against
  marimo comm/serialization regressions like 0.23.14 (#58).
- Packaging: sdist `README.md`/`LICENSE*` include patterns anchored to the
  repo root so nested READMEs (examples/, benchmarks/, perf/) no longer ship.

## [0.7.0] - 2026-07-11

### Added
- Self-building wheels: the JS bundle is compiled at package-build time by a
  hatchling hook (`hatch_build.py`); the bundle is no longer committed to git (#6)
- `scripts/check_versions.py` / `scripts/release.py` — single-source version
  across pyproject, js/package.json(+lock), and uv.lock, gated in CI and at
  publish time (#7, #11)
- ruff + pyright configured and enforced in CI; pytest-cov coverage (#8, #9)
- vitest suite for the JS modules (zoom gating, binary reconstruction,
  accessor resolution, perf tracker) (#10)
- `Map.set_layers(layers)` — replace layers and re-pack binary buffers in one
  call; the recommended reactive-update API (#30)
- Real `Map.fit_bounds(bounds, padding=)` via JS `map.fitBounds`, plus public
  `compute_bounds()` ported from deckgl_dash (#21)
- Public `pack_binary` / `pack_polygon_binary` exports (#29)
- `Map(show_perf_metrics=True)` opt-in for the FPS tracker (#24)
- Smoke tests for all geo/mesh layer wrappers (#27)
- `Makefile`, `CONTRIBUTING.md`, this changelog (#13)

### Changed
- marimo floor relaxed `>=0.23` → `>=0.22`: marimo 0.23 serializes large
  widget state ~3.6× slower at widget open (#58), so users on the JSON data
  path can stay on 0.22 until that's resolved upstream
- **Breaking:** zoom-gated visibility props renamed `min_zoom`/`max_zoom` →
  `visible_min_zoom`/`visible_max_zoom`; `TileLayer(min_zoom=, max_zoom=)`
  now reach deck.gl as real tile-fetch bounds (#22)
- **Breaking:** pandas removed from runtime dependencies (never imported);
  marimo is now an optional extra (`deckgl-marimo[marimo]`) used only by
  `as_widget()`; Python floor raised to 3.11; anywidget>=0.10,
  traitlets>=5.14, narwhals>=2 (via `narwhals.stable.v2`) (#16)
- `LineLayer`, `PointCloudLayer`, `SolidPolygonLayer` promoted to fully
  tested core layers (no more experimental warning); layer taxonomy is now
  15 tested + 17 experimental everywhere (#28)
- deck.gl pinned `~9.3.6`, maplibre-gl `~5.24.0`, esbuild `^0.28.1` (#14, #15)
- `layers/_core.py` refactored around a declarative `BINARY_ATTRIBUTES`
  table + shared packer/stripper; tuple→list prop normalization moved into
  `BaseLayer`; ~450 duplicated lines removed (#18)
- Pick-event row lookup is cached per layer (a click on a 1M-row layer no
  longer re-materializes the dataset every event) (#23)

### Removed
- **Breaking:** legacy `DeckGLHexagonWidget` (+ `widget.js`/`widget.css`) —
  use `HexagonLayer` + `Map` (#26)
- **Breaking:** unused `ViewState`, empty `controls/` package,
  `_utils.to_snake_case` (#25)

### Fixed
- `PolygonLayer.to_binary()` dead code path that packed every vertex twice
  on the ColorScale/callable path (#19)
- `Map.update_layer()` prop routing: no longer probes the layer with
  `hasattr` (which could silently no-op and instantiate a hidden Map);
  unknown props raise the "did you mean" error (#20)
- `Map.fit_bounds()` previously only centered — it now fits (#21)

## [0.6.1] - 2026-06

Historical release — see git history. Binary picking fixes; `as_widget()`
added on `Map` and `BaseLayer`.

## [0.6.0] - 2026-06

Historical release — see git history. Binary data transport
(`use_binary=True`, `pack_binary`), performance metrics, zoom-gated
visibility, ColorScale, composite layers (Displacement, Ellipse).
