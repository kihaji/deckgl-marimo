# Performance Comparison — post-merge (main @ 45e4000) vs baseline (9c3b5ee)

Rerun **2026-07-11**, same machine/browser/protocol as `PERF_BASELINE.md`
(identical harness `perf/perf_app.py` — zero API changes needed; payloads
byte-identical to baseline). Raw runs in `perf/results/postmerge/`.
Post-merge stack: all 20 review-wave PRs (#38–#57), deck.gl 9.3.6,
maplibre 5.24, **marimo 0.23.14** (was 0.22.0), anywidget 0.11.0 (was 0.9.21),
freshly built 3.0 MB bundle (was 2.65 MB — now includes DataFilterExtension +
editable-layers).

## Load-path medians (baseline → post-merge)

| Config | py build | canvas | settle | stalls total / max | heap |
|---|---|---|---|---|---|
| scatter 250k binary | 96 → 109 ms | 1.36 → 1.27 s | 1.58 → 1.61 s | 223/84 → 399/119 ms | 96 → 140 MB |
| scatter 250k json | 229 → **841 ms** ⚠ | 2.60 → 3.10 s | 2.86 → 3.46 s | 636/330 → 770/344 ms | 167 → 218 MB |
| scatter 1M binary | 441 → 407 ms | 2.50 → 2.53 s | 2.85 → 2.87 s | 295/111 → 432/123 ms | 139 → 189 MB |
| scatter 1M json | 954 → **3421 ms** ⚠ | 8.15 → 10.93 s | 8.53 → 11.28 s | 1790/1313 → 2032/1377 ms | 347 → 396 MB |
| polygon 50k binary | 50 → 38 ms | 1.16 → 1.04 s | 1.42 → 1.41 s | 309/97 → 446/109 ms | 168 → 207 MB |
| polygon 50k json | 114 → **414 ms** ⚠ | 1.60 → 1.78 s | 1.87 → 2.16 s | 511/117 → 589/125 ms | 186 → 228 MB |
| hexagon 500k json | 471 → **1661 ms** ⚠ | 4.46 → 5.73 s | 4.75 → 6.08 s | 1010/657 → 1120/723 ms | 227 → 268 MB |

Interaction after settle: unchanged — 58–60 fps, p95 frame 16.8 ms,
0–2 dropped frames, no long tasks, in every config.

## Widget-update lifecycle (250k binary + slider → `update_layer`) — the big win

| Metric | baseline | post-merge |
|---|---|---|
| Main-thread freeze per update | 1 × **~540 ms** | **0 long tasks** (never blocks >50 ms) |
| Heap churn per update | +170 MB transient (309→479 MB) | ~flat (180→188 MB) |
| Python `update_layer` | 122 ms | 155 ms (same repack path) |

The per-update UI freeze and memory churn from the baseline are gone — the
JS rebuild path (PR #41/#47 restructuring) no longer re-copies the binary
buffer / rebuilds layers in one blocking chunk.

## The JSON-mode ⚠ regression is marimo 0.23, not this repo's code

Every JSON-mode config got ~3.6× slower on Python-side build, scaling with N.
Isolation tests (same machine, same data):

| Configuration | build @250k json |
|---|---|
| old code + anywidget 0.9.21, plain script | 200 ms |
| old code + anywidget 0.11.0, plain script | 199 ms |
| merged code + anywidget 0.11.0, plain script | 206 ms |
| merged code inside **marimo 0.22.0** kernel | **253 ms** |
| merged code inside **marimo 0.23.14** kernel | **841 ms** |

The extra ~600 ms (250k) / ~2.5 s (1M) is spent inside marimo 0.23's comm/
serialization path when the widget opens with a large `layer_specs` state.
anywidget and this repo's code are exonerated. Binary mode is barely affected
because its synced state is ~500 bytes of spec + a raw buffer.

Follow-ups worth considering:
1. Report upstream to marimo (large widget-state comm-open regression 0.22→0.23,
   measurable as ~2.4 s extra kernel time for a 115 MB state).
2. The `marimo>=0.23` floor (pyproject) makes 0.23 the supported target — if the
   upstream fix lags, docs should steer large-data users to binary mode even
   harder (they should be there anyway; it's the library's core value prop).

## Other observations

- Binary-path load stalls grew ~100–150 ms total (e.g. 223→399 ms at 250k):
  consistent with the bundle growing 2.65→3.0 MB (extensions + editable-layers
  now bundled) plus the extra JS modules parsed at startup. Max single stall
  is still ~120 ms — no user-visible freeze. Steady-state heap is up ~40 MB
  across configs for the same reason.
- Python binary packing is neutral-to-faster (polygon 50 → 38 ms; 1M scatter
  441 → 407 ms) after the PR #47 declarative-attrs refactor and PR #42 numpy
  color expansion.
- Payload sizes, FPS, picking, and all rendering behavior are identical.
- First page load after a server restart runs ~500 ms slower (cold bundle
  cache); medians above exclude that first-run effect (run 1 of
  scatter-250k-binary retained in raw data for transparency).
