# Performance Baseline — pre-merge (main @ 9c3b5ee)

Baseline captured **2026-07-11** on `main` (9c3b5ee), *before* merging the 2026-07 review
wave (PRs #38–#57). Rerun the same protocol after the chain merges and compare.

## Environment

| | |
|---|---|
| Commit / branch | `9c3b5ee` / `main` |
| Python / marimo | 3.14.4 / 0.22.0 |
| deck.gl / maplibre-gl (resolved) | 9.3.1 / 5.24.0 (committed bundle) |
| Browser | Chrome 150 (WSLg), DPR 1, viewport 1905×2010 |
| GPU | NVIDIA RTX 5090 (ANGLE D3D12), 24 cores, 32 GB |
| Serving | `marimo run --headless` on `127.0.0.1:2718` (WSL2 localhost) |

## Method

Harness: `perf/perf_app.py` — one parameterized marimo notebook
(`PERF_SCENARIO` × `PERF_N` × `PERF_MODE` env vars), fixed seed 42, layers built
from identical `list[dict]` records in both modes (only `use_binary` differs).
Per config: fresh page load ×3, instrumented via injected JS
(buffered `PerformanceObserver` longtask + rAF frame trace + shadow-DOM canvas-mount
detection), then a fixed scripted interaction (2 pans + zoom-in/out ×3 ticks + 1 pan
over ~3 s of real mouse input). Values below are **medians of 3 runs**
(raw per-run JSON in `perf/results/baseline/`).

Metric definitions:

- **py build (ms)** — layer + `Map()` construction in the kernel (spec build + binary
  packing). Data generation excluded (timed separately). This is the "server compute"
  cost; marimo's HTTP TTFB was a flat 7–8 ms in every run and page assets loaded in
  &lt;350 ms, so kernel work + WS payload is what actually moves.
- **payload** — `len(binary_data)` or `len(json.dumps(layer_specs))` (goes over the
  marimo websocket).
- **canvas mount / settle (ms)** — navigation start → maplibre canvas created / end of
  the last load-phase long task (page fully interactive).
- **load stalls** — count / total / max of main-thread long tasks (>50 ms) during load.
- **interaction** — avg FPS, p95/max frame time, frames >50 ms, long tasks during the
  scripted pan/zoom window.
- **heap** — `performance.memory.usedJSHeapSize` after settle.

## Load-path results (medians)

| Config | py build | payload | canvas | settle | stalls (n / total / max) | heap |
|---|---|---|---|---|---|---|
| scatter 250k **binary** | 96 ms | **4.0 MB** | 1.36 s | 1.58 s | 3 / 223 / 84 ms | 96 MB |
| scatter 250k **json** | 229 ms | 28.7 MB | 2.60 s | 2.86 s | 5 / 636 / 330 ms | 167 MB |
| scatter 1M **binary** | 441 ms | **16.0 MB** | 2.50 s | 2.85 s | 3–4 / 295 / 111 ms | 139 MB |
| scatter 1M **json** | 954 ms | 114.7 MB | 8.15 s | 8.53 s | 5 / 1790 / **1313 ms** | 347 MB |
| polygon 50k **binary** | 50 ms | **2.6 MB** | 1.16 s | 1.42 s | 4 / 309 / 97 ms | 168 MB |
| polygon 50k **json** | 114 ms | 10.6 MB | 1.60 s | 1.87 s | 5 / 511 / 117 ms | 186 MB |
| hexagon 500k json (agg) | 471 ms | 57.4 MB | 4.46 s | 4.75 s | 5 / 1010 / 657 ms | 227 MB |

Binary vs JSON at the same N: **~7× smaller payload, ~2–3× faster time-to-map,
~3–6× less main-thread stall time, ~2.5× less heap**. The 1M JSON case freezes the
main thread for a contiguous **1.3 s** (JSON parse + layer build); 1M binary's worst
stall is ~110 ms.

## Interaction results (all configs)

Pan/zoom after settle is uniformly healthy on this GPU: **58–59 avg FPS,
p95 frame 16.8 ms, max frame ≤ 83 ms, 0–1 dropped frames (>50 ms), zero long tasks**
during the ~3 s scripted window — for every config including 1M JSON and extruded
hexagons. Rendering (GPU) is not the bottleneck on main; transport + parse is.

## Widget-update lifecycle (scatter 250k binary + slider → `update_layer`)

One slider step changes a single prop (`radius_scale`), which on main triggers a full
`_sync_layers()` repack + full binary resend + JS rebuild:

| Metric | median of 3 steps |
|---|---|
| Python `update_layer` (full repack) | 122 ms (first step 333 ms) |
| Click → UI settled | **1.13 s** |
| Main-thread freeze per update | 1 × **~540 ms** |
| Heap churn | +170 MB transient before GC (309→479→279 MB) |

This is the clearest regression target: a one-prop update costs the same as a full
reload's data path.

## Server response times

marimo HTTP: TTFB 7–8 ms (all runs), `domContentLoaded` 124–347 ms, static assets
&lt; 210 ms each. All layer data flows over the websocket, so its cost is captured in
the canvas/settle timeline, not in HTTP metrics. Nothing server-side is slow on
localhost; kernel compute (py build) is the only meaningful server-side variable.

## Rerun protocol (post-merge)

1. `PERF_SCENARIO=<scatter|polygon|hexagon|lifecycle> PERF_N=<n> PERF_MODE=<binary|json> uv run marimo run perf/perf_app.py --headless --port 2718`
   — the notebook may need API touch-ups after the merge (e.g. `set_layers`,
   `visible_min_zoom` renames); keep data gen, seeds, sizes, and displayed metrics identical.
2. Same browser instrumentation + interaction script (see `perf/results/baseline/*.json`
   for the exact shape); 3 runs per config, medians.
3. Compare against this table; flag any metric ±15 % or worse.

Configs: scatter 250k/1M × binary/json, polygon 50k × binary/json,
hexagon 500k json, lifecycle 250k binary (3 slider steps).

## Caveats

- Localhost WS transport: network latency ≈ 0, so payload-size effects show up as
  parse/copy stalls, not transfer time. Remote deployments would amplify the JSON gap.
- The browser tab must be focused during runs — background tabs throttle rAF and
  defer widget mount (first attempted run was discarded for this).
- `basemap="dark-matter"` tiles come from a CDN; tile fetches are excluded from the
  stall metrics (they're off-main-thread) but add visual variability between screenshots.
- Interaction FPS is GPU-bound headroom on an RTX 5090; weaker GPUs may differentiate
  configs that look identical here.
