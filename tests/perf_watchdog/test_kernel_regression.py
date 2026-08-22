"""Kernel-side performance watchdog (opt-in; NOT run by default or in CI).

Why this exists
---------------
marimo 0.23.14 made every anywidget comm open *and* every state update walk the
whole widget state (marimo-team/marimo#10127). For deckgl-marimo's JSON transport
mode that meant ``Map()`` construction and ``update_layer()`` got ~3.6× slower
for large data (deckgl-marimo#58, fixed upstream in 0.23.15 via #10254). Our
normal unit tests never saw it because the cost only appears *inside a marimo
kernel*, where the comm is real. This module runs the same workload twice:

1. **plain** — in this pytest process (no kernel, no comm): the cost of our own
   Python (spec build / binary packing).
2. **kernel** — inside a real marimo kernel, via ``marimo export html`` of
   ``_kernel_bench_notebook.py`` (no browser or headless display needed; the
   kernel executes the notebook and the comm path is exercised exactly as it
   is in ``marimo run``/``edit``).

and asserts ``kernel / plain`` stays below a ceiling. Ratios are machine-
independent (both sides run on the same box, minutes apart), which is what
makes this usable as a watchdog rather than a benchmark.

Calibration (250k rows, 2026-08-21, tests/perf_watchdog/_bench.py workload)::

    metric          marimo 0.22.0  0.24.0   0.23.14 (regressed)
    json build          1.35x       1.38x        4.35x
    json update         1.25x       1.23x        4.23x
    binary build        1.00x       1.22x        1.18x   (control)
    binary update       1.05x       1.08x        1.07x   (control)

Ceiling is 2.0x (``DECKGL_PERF_MAX_RATIO`` to override).

Running
-------
::

    make test-perf                      # or:
    uv run pytest --run-perf tests/perf_watchdog -v
    DECKGL_PERF_N=100000 uv run pytest --run-perf tests/perf_watchdog   # quicker
    uv run --with marimo==0.23.14 pytest --run-perf tests/perf_watchdog # should FAIL

Takes ~15–25 s (one marimo kernel subprocess + ~2 s in-process). Skipped
unless ``--run-perf`` is passed or ``DECKGL_RUN_PERF=1`` is set — see
``tests/conftest.py``. Deliberately excluded from CI: timing assertions on shared
runners are flaky and the value here is catching upstream regressions when
bumping marimo locally, not gating PRs. Set ``DECKGL_PERF_RESULTS_DIR`` to also
dump the raw numbers as JSON for later comparison.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

from . import _bench

pytestmark = pytest.mark.perf

HERE = Path(__file__).resolve().parent
NOTEBOOK = HERE / "_kernel_bench_notebook.py"

N = int(os.environ.get("DECKGL_PERF_N", str(_bench.DEFAULT_N)))
MAX_RATIO = float(os.environ.get("DECKGL_PERF_MAX_RATIO", "2.0"))
METRICS = ("json_build_ms", "json_update_ms", "binary_build_ms", "binary_update_ms")


def _run_in_kernel(tmp_path: Path) -> dict[str, Any]:
    """Execute the bench notebook in a marimo kernel and return its timings."""
    out = tmp_path / "kernel_bench.json"
    html = tmp_path / "kernel_bench.html"
    env = {**os.environ, "DECKGL_PERF_N": str(N), "DECKGL_PERF_OUT": str(out)}
    cmd = [
        sys.executable,
        "-m",
        "marimo",
        "export",
        "html",
        str(NOTEBOOK),
        "-o",
        str(html),
        "--no-include-code",
    ]
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=900)
    if not out.exists():
        pytest.fail(f"kernel bench produced no output (exit {proc.returncode}).\ncmd: {' '.join(cmd)}\nstderr (tail):\n{proc.stderr[-3000:]}")
    # marimo 0.22's exporter returns non-zero when it cannot render the widget
    # cell, after the timings have already been written; that is not a failure.
    return json.loads(out.read_text())


@pytest.fixture(scope="module")
def bench_results(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    pytest.importorskip("marimo")
    pytest.importorskip("numpy")
    tmp_path = tmp_path_factory.mktemp("perf_watchdog")

    records = _bench.make_records(N)
    plain = _bench.bench(records)
    plain.pop("_map", None)
    del records

    kernel = _run_in_kernel(tmp_path)

    ratios = {m: round(kernel[m] / plain[m], 2) for m in METRICS}
    results = {
        "n": N,
        "marimo": kernel.get("marimo"),
        "max_ratio": MAX_RATIO,
        "plain": plain,
        "kernel": kernel,
        "ratios": ratios,
    }

    lines = [
        f"perf watchdog — marimo {results['marimo']}, N={N}, ceiling {MAX_RATIO}x",
        f"{'metric':18} {'plain':>9} {'kernel':>9} {'ratio':>7}",
    ]
    for m in METRICS:
        lines.append(f"{m:18} {plain[m]:>8.1f}ms {kernel[m]:>8.1f}ms {ratios[m]:>6.2f}x")
    results["table"] = "\n".join(lines)
    print("\n" + results["table"])

    if dump_dir := os.environ.get("DECKGL_PERF_RESULTS_DIR"):
        Path(dump_dir).mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        (Path(dump_dir) / f"watchdog_{stamp}_marimo{results['marimo']}.json").write_text(
            json.dumps({k: v for k, v in results.items() if k != "table"}, indent=1)
        )
    return results


@pytest.mark.parametrize("metric", METRICS)
def test_kernel_overhead_within_ceiling(bench_results: dict[str, Any], metric: str, record_property: Any) -> None:
    """kernel-time / plain-time for this metric must stay below MAX_RATIO.

    json_* are the sentinels for the marimo 0.23.14-style regression (large
    synced state serialised on comm open / send). binary_* are controls: their
    synced state is ~500 B + a raw buffer, so a jump there points at general
    kernel overhead rather than state-size scaling.
    """
    ratio = bench_results["ratios"][metric]
    record_property(f"ratio_{metric}", ratio)
    record_property(f"plain_{metric}", bench_results["plain"][metric])
    record_property(f"kernel_{metric}", bench_results["kernel"][metric])
    assert ratio < MAX_RATIO, (
        f"{metric}: kernel {bench_results['kernel'][metric]:.1f} ms vs plain "
        f"{bench_results['plain'][metric]:.1f} ms = {ratio:.2f}x (ceiling {MAX_RATIO}x) "
        f"under marimo {bench_results['marimo']} at N={bench_results['n']}.\n"
        "Kernel-side widget cost has regressed relative to our own Python work — "
        "most likely marimo's comm/serialisation path (cf. deckgl-marimo#58).\n" + bench_results["table"]
    )


def test_json_state_cost_is_not_dominated_by_kernel(bench_results: dict[str, Any]) -> None:
    """Same signal expressed as absolute overhead rather than a ratio.

    (kernel_json - plain_json) is the extra cost of shipping ~28 MB of JSON
    state through the kernel on comm open; it is legitimately non-zero, but if
    it exceeds MAX_RATIO × plain_json something is walking/re-serialising the
    whole state (healthy ≈ 0.3–0.4× plain; marimo 0.23.14 ≈ 3.3× plain).
    """
    p, k = bench_results["plain"], bench_results["kernel"]
    overhead = k["json_build_ms"] - p["json_build_ms"]
    assert overhead < MAX_RATIO * p["json_build_ms"], (
        f"JSON-mode kernel overhead {overhead:.1f} ms exceeds {MAX_RATIO}x the plain "
        f"build ({p['json_build_ms']:.1f} ms) under marimo {bench_results['marimo']}.\n" + bench_results["table"]
    )
