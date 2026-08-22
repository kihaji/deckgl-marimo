"""marimo notebook executed by tests/perf_watchdog/test_kernel_regression.py.

Runs the shared ``_bench`` workload *inside a marimo kernel* (via
``marimo export html``) so that Map construction opens a real anywidget comm
and ``update_layer`` goes through marimo's comm send path — the code path
that regressed in marimo 0.23.14 (deckgl-marimo#58 / marimo-team/marimo#10144).

Env:
    DECKGL_PERF_N    row count (default 250000)
    DECKGL_PERF_OUT  path to write the timings JSON to (required)

Not collected by pytest (no ``test_`` prefix). Can be run by hand:

    DECKGL_PERF_OUT=/tmp/k.json uv run marimo export html \
        tests/perf_watchdog/_kernel_bench_notebook.py -o /tmp/k.html --no-include-code
"""

import marimo

app = marimo.App(width="full")


@app.cell
def _():
    import json
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import _bench as bench  # noqa: E402

    import marimo as mo

    N = int(os.environ.get("DECKGL_PERF_N", str(bench.DEFAULT_N)))
    OUT = os.environ["DECKGL_PERF_OUT"]
    return N, OUT, bench, json, mo


@app.cell
def _(N, bench):
    records = bench.make_records(N)
    return (records,)


@app.cell
def _(OUT, bench, json, mo, records):
    results = bench.bench(records)
    widget = results.pop("_map")
    results["marimo"] = mo.__version__
    with open(OUT, "w") as _f:
        json.dump(results, _f)
    mo.Html(f'<pre id="py-metrics">{json.dumps(results)}</pre>')
    return (widget,)


@app.cell
def _(widget):
    widget
    return


if __name__ == "__main__":
    app.run()
