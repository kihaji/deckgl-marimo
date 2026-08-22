# perf/ — browser-side performance harness and results

Not part of the Python package (wheel packages only `src/deckgl_marimo`; the
sdist has an explicit include list) and not run in CI. The opt-in kernel-side
watchdog lives separately in `tests/perf_watchdog/` (`make test-perf`).

| Path | What |
|---|---|
| `perf_app.py` | Parameterized marimo notebook (`PERF_SCENARIO`, `PERF_N`, `PERF_MODE`) that exposes Python-side timings in `#py-metrics`. |
| `tools/browser_protocol.md` | The exact browser instrumentation (injected JS, waits, scripted pan/zoom, collectors). |
| `tools/start_server.sh`, `tools/save_runs.py` | Helpers to cycle the server per config and persist collected runs. |
| `results/{baseline,postmerge,marimo024}/` | Raw per-run JSON + `environment.json` for each snapshot. |
| `PERF_BASELINE.md` | 2026-07-11, main @ 9c3b5ee, marimo 0.22.0 — pre review-wave baseline. |
| `PERF_POSTMERGE.md` | 2026-07-11, main @ 45e4000, marimo 0.23.14 — post review-wave; found the JSON-mode regression (#58). |
| `PERF_MARIMO024.md` | 2026-08-21, main @ f1a7f07 (v0.7.0), marimo 0.24.0 — regression confirmed gone. |
| `upstream/` | Minimal repros used for marimo-team/marimo#10144 (historical; `repro_widget_ref_perf.py` no longer imports on ≥0.23.15). |
