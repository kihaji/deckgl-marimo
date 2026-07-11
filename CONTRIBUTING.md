# Contributing to deckgl-marimo

## Prerequisites

- Python 3.11+ and [uv](https://docs.astral.sh/uv/)
- Node.js 20+ (see `.nvmrc`) and npm — required to build the JS bundle

## Getting started

```bash
git clone https://github.com/kihaji/deckgl-marimo
cd deckgl-marimo

# JS bundle (the widget frontend) — build it once
cd js && npm ci && npm run build && cd ..

# Python environment (editable install; skips the JS build when the
# bundle already exists)
uv sync --extra dev
```

## Dev loop

The widget is a single anywidget: Python (`src/deckgl_marimo/`) serializes
layer specs and binary buffers; JS (`js/src/`) renders them with deck.gl on
a MapLibre basemap.

**Python changes** — the editable install picks them up immediately; run a
marimo notebook from `examples/` to try them:

```bash
uv run marimo edit examples/01_scatterplot.py
```

**JS changes** — rebuild the bundle on save in a second terminal:

```bash
make watch        # = cd js && npm run watch
```

then hard-refresh the notebook page. The bundle
(`src/deckgl_marimo/static/deckgl-marimo.bundle.js|css`) is a build
product and is **not** committed to git; wheels build it automatically at
package-build time via `hatch_build.py` (set
`DECKGL_MARIMO_SKIP_JS_BUILD=1` to skip when the bundle is prebuilt).

## Tests and quality gates

```bash
make test         # pytest (tests/)
make test-js      # vitest (js/src/__tests__/)
make quality      # ruff + pyright
make check-versions
```

CI runs all of the above plus `uv lock --check` on Python 3.11–3.14, and
builds a wheel through the self-building hook. Everything must be green.

## Conventions

- Python is snake_case; props convert to deck.gl camelCase at spec time
  (`to_camel_case`). Accessor props are named `get_*`.
- Public modules re-export through `src/deckgl_marimo/__init__.py`;
  implementation modules are underscore-prefixed.
- numpy-style docstrings.
- New layer wrappers: declare `LAYER_TYPE`, keyword-only `__init__`
  params (they double as the valid-prop list for typo validation), and a
  `BINARY_ATTRIBUTES` table if the layer supports binary transport (see
  `layers/_binary_attrs.py`).
- Add tests beside the code you change; marimo notebooks in `examples/`
  are runnable documentation — keep them working.

## Releasing (maintainers)

```bash
uv run python scripts/release.py 0.7.0   # bump everywhere + verify + commit + tag
git push && git push --tags
```

Then publish a GitHub Release from the tag — the `publish.yml` workflow
verifies the tag matches the package version, builds via the hatch hook,
and publishes to PyPI with OIDC trusted publishing. Update `CHANGELOG.md`
as part of the release commit.
