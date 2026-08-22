# Performance Rerun — marimo 0.24.0 (main @ f1a7f07 / v0.7.0)

Rerun **2026-08-21** of the protocol in `PERF_BASELINE.md` / `PERF_POSTMERGE.md`
(same harness `perf/perf_app.py`, same browser instrumentation, same machine,
3 fresh loads per config + scripted pan/zoom; medians). Raw runs in
`perf/results/marimo024/`. The browser protocol and helper scripts are now
checked into `perf/tools/` so this can be replayed without transcript archaeology.

**Purpose:** the post-merge run (2026-07-11) found a ~3.6× Python-side slowdown
in every JSON-mode config and traced it to marimo 0.23.14 (deckgl-marimo#58,
upstream marimo-team/marimo#10144). marimo has since shipped 0.23.15 (fix:
marimo-team/marimo#10254, removed the per-comm recursive state scan) and 0.24.0.
This rerun measures the full suite on the latest release.

## Environment

| | baseline (07-11) | post-merge (07-11) | **this run (08-21)** |
|---|---|---|---|
| deckgl-marimo | 9c3b5ee | 45e4000 | **f1a7f07 (v0.7.0)** — same code as post-merge + floor/version bumps |
| marimo | 0.22.0 | 0.23.14 | **0.24.0** (`uv run --with marimo==0.24.0`) |
| anywidget | 0.9.21 | 0.11.0 | 0.11.0 |
| deck.gl / maplibre-gl | 9.3.1 / 5.24.0 | 9.3.6 / 5.24.0 | 9.3.6 / 5.24.0 (bundle 3.18 MB, unchanged) |
| Python / Chrome / GPU | 3.14.4 / 150 / RTX 5090 | same | same (viewport 1905×2010, DPR 1) |

## Load-path medians (baseline → post-merge → **marimo 0.24.0**)

| Config | py build | canvas | settle | stalls n / total / max | heap |
|---|---|---|---|---|---|
| scatter 250k binary | 96 → 109 → **133 ms** | 1.36 → 1.27 → **1.38 s** | 1.58 → 1.61 → **1.73 s** | 3/223/84 → 4/399/119 → **6/395/92** | 96 → 140 → **100 MB** |
| scatter 250k json | 229 → ⚠841 → **253 ms** | 2.60 → 3.10 → **2.47 s** | 2.86 → 3.46 → **2.85 s** | 5/636/330 → 6/770/344 → **6/751/335** | 167 → 218 → **164 MB** |
| scatter 1M binary | 441 → 408 → **548 ms** | 2.50 → 2.53 → **2.69 s** | 2.85 → 2.87 → **3.07 s** | 3/295/111 → 5/432/123 → **5/379/131** | 139 → 189 → **157 MB** |
| scatter 1M json | 954 → ⚠3421 → **963 ms** | 8.15 → 10.93 → **8.30 s** | 8.53 → 11.28 → **8.64 s** | 5/1790/1313 → 6/2032/1377 → **6/2051/1417** | 347 → 396 → **357 MB** |
| polygon 50k binary | 50 → 38 → **34 ms** | 1.16 → 1.04 → **1.05 s** | 1.42 → 1.41 → **1.43 s** | 4/309/97 → 5/446/109 → **5/462/125** | 168 → 207 → **174 MB** |
| polygon 50k json | 114 → ⚠414 → **117 ms** | 1.60 → 1.78 → **1.45 s** | 1.87 → 2.16 → **1.80 s** | 5/511/117 → 6/589/125 → **6/569/121** | 186 → 228 → **210 MB** |
| hexagon 500k json | 471 → ⚠1661 → **482 ms** | 4.46 → 5.73 → **4.54 s** | 4.75 → 6.08 → **4.94 s** | 5/1010/657 → 5/1120/723 → **7/1315/704** | 227 → 268 → **232 MB** |

Payloads are byte-identical to both earlier runs (binary 4.0 / 16.0 / 2.6 MB; JSON
28.7 / 114.7 / 10.6 / 57.4 MB). Run 1 of every config is the cold-bundle-cache load and
is kept in the raw data; medians of runs 2–3 alone are within a few % of the
3-run medians above (e.g. 250k json build 252 ms, 1M json canvas 8.49 s).

### Interaction (all configs)

Unchanged from both prior runs: **58–60 avg fps, p95 frame 16.8 ms, max frame
≤ 67 ms, 0–1 dropped frames, zero long tasks** during the ~3 s pan/zoom window —
including 1M JSON and extruded hexagons. Rendering is still GPU-headroom-bound;
transport + parse remains the only cost that moves.

## Widget-update lifecycle (250k binary + slider → `update_layer`)

| Metric | baseline | post-merge | **marimo 0.24.0** |
|---|---|---|---|
| Main-thread freeze per update | 1 × ~540 ms | 0 long tasks | **0 long tasks** |
| Heap across 3 updates | +170 MB churn (309→479 MB) | flat 180→188 MB | **flat 141→145→140 MB** |
| Python `update_layer` (median of 3) | 122 ms | 155 ms | **133 ms** (191 / 133 / 109) |
| Canvas mount | — | 1.24 s | 1.45 s |

The post-merge lifecycle win holds on 0.24.0.

## Findings

1. **The JSON-mode regression is gone.** Every ⚠ config is back to baseline
   (0.22.0) levels: 250k scatter 841 → 253 ms, 1M scatter 3421 → 963 ms,
   polygon 414 → 117 ms, hexagon 1661 → 482 ms. Canvas/settle times follow:
   1M JSON time-to-map 10.9 → 8.3 s, hexagon 5.7 → 4.5 s. This is the upstream
   fix (marimo-team/marimo#10254, shipped 0.23.15) carried forward into 0.24.0;
   marimo 0.23.14 remains the only affected release.

2. **Binary-mode py build is marimo-independent; the small drift is noise.**
   Medians came in 20–35 % above post-merge (250k 109 → 133 ms; 1M 408 → 548 ms)
   but with wide run-to-run spread (1M runs: 548 / 387 / 649 ms). A kernel-only
   A/B via `marimo export html` on the same day gives 1M-binary build
   **0.23.14 = 562–578 ms vs 0.24.0 = 563–588 ms** (4 runs each) — identical, and
   both above July's browser-measured 408 ms, i.e. day-to-day machine variance,
   not marimo 0.24. Binary-mode canvas/settle are within ±0.2 s of both earlier runs.

3. **Steady-state heap dropped back toward baseline** in every config (e.g.
   250k binary 140 → 100 MB, 250k json 218 → 164 MB, 1M binary 189 → 157 MB).
   Our bundle is unchanged, so this is marimo 0.24's frontend holding less;
   it reverses the +40 MB noted post-merge.

4. **Load stalls are the same shape as post-merge** (totals within ±10 %, max
   stall 92–131 ms binary / up to 1.4 s for 1M JSON parse). The 1M-JSON 1.3–1.4 s
   contiguous main-thread freeze is inherent to parsing a 115 MB JSON state in the
   browser and is present in all three runs — binary mode (max stall ~130 ms for
   the same 1M rows) remains the answer for large data, as before.

5. Nothing in this run is ±15 % worse than baseline except binary py build
   (see 2 — not attributable to marimo) and hexagon stall total (1010 → 1315 ms,
   driven by run 1/3 cold-ish variance; run 2 was 1066 ms).

## Follow-ups

- marimo 0.24.0 is fully supported by the current `marimo>=0.22` floor; no
  pin change needed. Users on large JSON-mode data should avoid exactly 0.23.14.
- `perf/upstream/repro_widget_ref_perf.py` is obsolete (the module it imports
  was deleted upstream); `perf/upstream/repro_notebook.py` is still the minimal repro.
- To rerun: `perf/tools/browser_protocol.md` + `perf/tools/start_server.sh` +
  `perf/tools/save_runs.py` (set `PERF_RESULTS_DIR`).
