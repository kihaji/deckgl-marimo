# Installation

```bash
pip install deckgl-marimo
# or
uv add deckgl-marimo
```

Requires Python 3.11+.

## Extras

| Extra | Installs | When you need it |
|---|---|---|
| `deckgl-marimo[binary]` | numpy | Binary data transport (`use_binary=True`, `pack_binary`) |
| `deckgl-marimo[marimo]` | marimo | `Map.as_widget()` outside an existing marimo environment |

Inside a marimo notebook, marimo is already present — the extra exists for
completeness. The core install is deliberately small (anywidget, traitlets,
narwhals); bring whichever DataFrame library you already use.

## Installing from source

Building from a git checkout or sdist compiles the JS bundle at install
time and requires **Node.js 20+**:

```bash
git clone https://github.com/kihaji/deckgl-marimo
cd deckgl-marimo
uv pip install .
```

Prebuilt wheels from PyPI never need Node. See
[CONTRIBUTING](https://github.com/kihaji/deckgl-marimo/blob/main/CONTRIBUTING.md)
for the development setup.
