"""Minimal end-to-end repro: anywidget with a large synced trait in marimo.

Times widget construction (which opens the comm and serializes state) inside
a marimo kernel. Requires only marimo + anywidget.

    uv run --no-project --with marimo==0.23.14 --with anywidget \
        marimo run repro_notebook.py --headless --port 2719

Read the timing from the page's <pre id="py-metrics"> element.
"""

import marimo

app = marimo.App(width="full")


@app.cell
def _():
    import json
    import time

    import anywidget
    import traitlets

    import marimo as mo

    N = 250_000

    class BigStateWidget(anywidget.AnyWidget):
        _esm = """
        export default {
          render({ model, el }) {
            el.textContent = `rows: ${model.get("data").length}`;
          }
        }
        """
        data = traitlets.List([]).tag(sync=True)

    records = [
        {
            "lon": -100.0 + i * 1e-5,
            "lat": 40.0,
            "color": [255, 0, 0, 180],
            "value": float(i),
        }
        for i in range(N)
    ]

    _t0 = time.perf_counter()
    widget = BigStateWidget(data=records)
    create_ms = (time.perf_counter() - _t0) * 1000

    _t0 = time.perf_counter()
    widget.data = records[: N // 2]
    update_ms = (time.perf_counter() - _t0) * 1000

    payload = {
        "marimo": mo.__version__,
        "n": N,
        "widget_create_ms": round(create_ms, 1),
        "trait_update_ms": round(update_ms, 1),
    }
    mo.Html(f'<pre id="py-metrics">{json.dumps(payload)}</pre>')
    return (widget,)


@app.cell
def _(widget):
    widget
    return


if __name__ == "__main__":
    app.run()
