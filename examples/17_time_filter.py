# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "numpy",
#     "deckgl-marimo",
# ]
#
# [tool.uv.sources]
# deckgl-marimo = { path = ".." }
# ///
"""GPU time filter: animated sliding window over 100k points.

The DataFilterExtension filters on the GPU — the animation never
re-serializes data. Also shows the pure-reactive alternative (a marimo
slider driving `filter_range` directly).
"""

import marimo

__generated_with = "0.22.0"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import numpy as np

    import deckgl_marimo as dgl

    return dgl, mo, np


@app.cell
def _(np):
    # 100k points drifting across Europe over t in [0, 100)
    rng = np.random.default_rng(7)
    n = 100_000
    t = rng.uniform(0, 100, n)
    data = [
        {
            "lon": float(-10 + 0.3 * t[i] + rng.normal(0, 1.5)),
            "lat": float(42 + 0.08 * t[i] + rng.normal(0, 1.0)),
            "t": float(t[i]),
        }
        for i in range(n)
    ]
    return (data,)


@app.cell
def _(mo):
    playing = mo.ui.switch(value=True, label="Play")
    window = mo.ui.slider(2, 30, value=10, show_value=True, label="Window (t units)")
    mo.hstack([playing, window], justify="start", gap=2)
    return playing, window


@app.cell
def _(data, dgl):
    # Stable map cell — one layer with a GPU filter accessor. The
    # DataFilterExtension attaches automatically.
    deck_map = dgl.Map(basemap="dark-matter", center=(5, 47), zoom=4)
    deck_map.set_layers([
        dgl.ScatterplotLayer(
            data=data,
            get_position=["lon", "lat"],
            get_fill_color=[0, 200, 255, 180],
            radius_min_pixels=2,
            get_filter_value="t",
        )
    ])
    widget = deck_map.as_widget()
    domain = dgl.compute_time_domain(data, "t")
    return deck_map, domain, widget


@app.cell
def _(widget):
    widget
    return


@app.cell
def _(deck_map, dgl, domain, playing, window):
    # Reactive: play/pause and window width update the client-side animation
    deck_map.time_filter = dgl.build_time_filter(
        domain,
        window=window.value,
        playing=playing.value,
        soft_edge=window.value * 0.2,
    )
    return


@app.cell
def _(mo, widget):
    mo.md(f"Playback head: **t = {widget.value.get('current_time', 0):.1f}**")
    return


if __name__ == "__main__":
    app.run()
