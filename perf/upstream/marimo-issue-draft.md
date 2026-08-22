# DRAFT — upstream issue for marimo-team/marimo (do not submit yet)

**Title:** anywidget widget creation and state updates ~3.6× slower in 0.23.14 for large synced traits (regression from #10127)

---

## Describe the bug

marimo 0.23.14 made creating an anywidget — and every subsequent state update — dramatically slower when the widget syncs a large JSON-serializable trait (e.g. a list of records). 0.23.13 and earlier are unaffected.

Measured inside a `marimo run` kernel with a minimal anywidget carrying a 250,000-record list trait (script below):

| marimo | widget create | trait update |
|---|---|---|
| 0.23.13 | 229 ms | 248 ms |
| **0.23.14** | **831 ms** | **587 ms** |

The extra cost scales linearly with the size of the synced state (~2.5 s extra at 1M records) and is paid on **every** comm open and **every** update of the widget.

We hit this in [deckgl-marimo](https://github.com/kihaji/deckgl-marimo) (kihaji/deckgl-marimo#58), where post-upgrade benchmarks showed every JSON-mode map load slowing 3.6× across scatter/polygon/hexagon scenarios; bisecting marimo versions isolated it to 0.23.14 exactly. Any data-heavy anywidget that syncs records as JSON (lonboard/mosaic-style JSON paths, table widgets, etc.) is affected the same way.

## Cause

#10127 (`56d8ec070`, "Support anywidget composition and hot reload") routes every anywidget comm open and send through `AnyWidgetStateSerializer.serialize()` → `_replace_widget_refs()` (`marimo/_plugins/ui/_impl/anywidget/widget_ref.py`), which — to find embedded child widgets — recursively visits **every node** of the state and:

1. probes each node with `_try_get_widget_model_id()` (a `getattr(value, "model_id")` plus `MimeBundleDescriptor` type checks) *before* the primitive early-out, and
2. rebuilds a parallel copy of every dict/list/tuple, then compares element identity to decide whether to keep the original — allocating and discarding a full copy of every container even when nothing was replaced.

For a 250k-record trait that is ~1.5M probed nodes and ~500k throwaway container allocations per open/update. The walk alone microbenchmarks at ~414 ms:

```python
# uv run --with marimo==0.23.14 python thisfile.py
import time
from marimo._plugins.ui._impl.anywidget.widget_ref import AnyWidgetStateSerializer

state = {
    "_esm": "export default { render({ model, el }) {} }",
    "data": [
        {"lon": -100.0 + i * 1e-5, "lat": 40.0, "color": [255, 0, 0, 180], "value": float(i)}
        for i in range(250_000)
    ],
}
s = AnyWidgetStateSerializer(state)
t0 = time.perf_counter()
s.serialize(state)
print(f"{(time.perf_counter() - t0) * 1000:.0f} ms")  # ~414 ms
```

## Reproduction (end-to-end)

```python
# repro.py — run: uv run --with marimo==0.23.14 --with anywidget marimo run repro.py
import marimo

app = marimo.App()

@app.cell
def _():
    import time, anywidget, traitlets
    import marimo as mo

    class BigStateWidget(anywidget.AnyWidget):
        _esm = """
        export default {
          render({ model, el }) { el.textContent = `rows: ${model.get("data").length}`; }
        }
        """
        data = traitlets.List([]).tag(sync=True)

    records = [
        {"lon": -100.0 + i * 1e-5, "lat": 40.0, "color": [255, 0, 0, 180], "value": float(i)}
        for i in range(250_000)
    ]

    t0 = time.perf_counter()
    widget = BigStateWidget(data=records)
    create_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    widget.data = records[:125_000]
    update_ms = (time.perf_counter() - t0) * 1000

    mo.md(f"create: {create_ms:.0f} ms — update: {update_ms:.0f} ms")
    return (widget,)

@app.cell
def _(widget):
    widget
    return
```

Swap `marimo==0.23.14` for `marimo==0.23.13` to see the before/after.

## Proposed fix

The walk's semantics can be kept while removing the pathological constant (we have a patch ready; happy to open a PR):

1. **Leaf fast-path first** — `str/int/float/bool/bytes/None` return before any `getattr` probing; large data traits are overwhelmingly made of these.
2. **Don't probe plain containers** — widgets are `HasTraits`/descriptor-carrying objects, never `dict`/`list`/`tuple` instances, so containers can be recursed into without the `model_id`/descriptor probe.
3. **Copy lazily** — copy a container only on the first actual replacement inside it instead of rebuild-then-compare, so the (typical) widget-free state costs zero allocations.

With that patch on top of 0.23.14 (same repro): create 831 → **359 ms**, update 587 → **335 ms**; `serialize()` alone 414 → 119 ms. The remaining ~120 ms at 250k records is the irreducible pure-Python traversal — if that still feels too high, options are restricting the composition scan to top-level trait values or documenting binary buffers (`DataView`/bytes, which are not walked) as the big-data path.

## Environment

- marimo 0.23.14 (regression bisected to exactly this version; 0.23.13 fine)
- anywidget 0.11.0, ipywidgets 8.1.8, traitlets 5.14.3, Python 3.13/3.14, Linux

---

# DRAFT — PR description (for the fix branch `perf/widget-ref-fast-walk`)

**This pull request was authored by a coding agent.** *(required disclosure per AGENTS.md; PR must be opened as draft)*

**Title:** perf: make anywidget state serialization cheap for large widget-free states

Fixes #<issue-number-above>.

#10127 routed every anywidget comm open and send through `_replace_widget_refs()`, which probed every node of the state with `getattr` before its primitive early-out and rebuilt a parallel copy of every container just to compare element identity. For data-heavy widgets (250k-record list trait) that made widget creation ~3.6× slower and added the same cost to every state update.

This PR reorders the walk (leaves first, containers recursed without probing, objects probed last) and makes container copies lazy (copy-on-first-replacement). Composition semantics are unchanged: widgets are still found and replaced at any depth, sibling subtrees keep identity, and the input state is never mutated. The only behavioral delta is that a hypothetical widget implemented as a `dict`/`list`/`tuple` subclass would no longer be replaced — widgets are `HasTraits`/descriptor objects, so this cannot occur.

Numbers (250k-record list trait, median of 5):

| | 0.23.13 | 0.23.14 | this PR |
|---|---|---|---|
| widget create (in kernel) | 229 ms | 831 ms | 359 ms |
| trait update (in kernel) | 248 ms | 587 ms | 335 ms |
| `serialize()` microbench | n/a | 414 ms | 119 ms |

Adds `tests/_plugins/ui/_impl/anywidget/test_widget_ref.py` (replacement at depth, identity preservation, lazy copying, tuple round-trip, serializer gating) — the module previously had no direct tests. `uv run --group test-optional pytest tests/_plugins/ui/_impl/{anywidget,test_comm.py,test_anywidget.py}`: 86 passed. `ruff check`/`format` clean; `make py-check` errors are pre-existing on main.
