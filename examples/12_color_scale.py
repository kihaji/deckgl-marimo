# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pandas",
#     "deckgl-marimo",
#     "marimo",
# ]
#
# [tool.uv.sources]
# deckgl-marimo = { path = ".." }
# ///

import marimo

__generated_with = "0.22.0"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    import pandas as pd
    import random

    return pd, random


@app.cell
def _():
    import deckgl_marimo as dgl

    return (dgl,)


@app.cell
def _(mo, pd, random):
    random.seed(42)
    n = 500
    df = pd.DataFrame(
        {
            "lon": [random.uniform(-122.5, -122.3) for _ in range(n)],
            "lat": [random.uniform(37.6, 37.85) for _ in range(n)],
            "temperature": [random.uniform(0, 100) for _ in range(n)],
        }
    )
    mo.md(f"**ColorScale Demo** — {len(df):,} points with random temperatures (0–100)")
    return (df,)


@app.cell
def _(mo):
    mo.md("""
    ### 1. Named palette — Viridis
    """)
    return


@app.cell
def _(dgl, mo):
    map1 = dgl.Map(basemap="dark-matter", center=(-122.4, 37.75), zoom=11)
    widget1 = map1.as_widget()
    return map1, widget1


@app.cell
def _(widget1):
    widget1
    return


@app.cell
def _(df, dgl, map1):
    map1.layer_specs = [
        dgl.ScatterplotLayer(
            data=df.to_dict("records"),
            get_position=["lon", "lat"],
            get_fill_color=dgl.ColorScale("temperature", palette="viridis"),
            get_radius=1,
            radius_min_pixels=4,
            radius_max_pixels=15,
            opacity=0.9,
        ).to_spec()
    ]
    return


@app.cell
def _(mo):
    mo.md("""
    ### 2. Two-color ramp — Blue to Red
    """)
    return


@app.cell
def _(dgl, mo):
    map2 = dgl.Map(basemap="dark-matter", center=(-122.4, 37.75), zoom=11)
    widget2 = map2.as_widget()
    return map2, widget2


@app.cell
def _(widget2):
    widget2
    return


@app.cell
def _(df, dgl, map2):
    map2.layer_specs = [
        dgl.ScatterplotLayer(
            data=df.to_dict("records"),
            get_position=["lon", "lat"],
            get_fill_color=dgl.ColorScale(
                "temperature", colors=["blue", "red"]
            ),
            get_radius=1,
            radius_min_pixels=4,
            radius_max_pixels=15,
            opacity=0.9,
        ).to_spec()
    ]
    return


@app.cell
def _(mo):
    mo.md("""
    ### 3. Log scale — Plasma palette
    """)
    return


@app.cell
def _(dgl, mo):
    map3 = dgl.Map(basemap="dark-matter", center=(-122.4, 37.75), zoom=11)
    widget3 = map3.as_widget()
    return map3, widget3


@app.cell
def _(widget3):
    widget3
    return


@app.cell
def _(df, dgl, map3):
    map3.layer_specs = [
        dgl.ScatterplotLayer(
            data=df.to_dict("records"),
            get_position=["lon", "lat"],
            get_fill_color=dgl.ColorScale(
                "temperature", palette="plasma", scale="log"
            ),
            get_radius=1,
            radius_min_pixels=4,
            radius_max_pixels=15,
            opacity=0.9,
        ).to_spec()
    ]
    return


@app.cell
def _(mo):
    mo.md("""
    ### 4. Callable accessor — Custom color function
    """)
    return


@app.cell
def _(dgl, mo):
    map4 = dgl.Map(basemap="dark-matter", center=(-122.4, 37.75), zoom=11)
    widget4 = map4.as_widget()
    return map4, widget4


@app.cell
def _(widget4):
    widget4
    return


@app.cell
def _(df, dgl, map4):
    map4.layer_specs = [
        dgl.ScatterplotLayer(
            data=df.to_dict("records"),
            get_position=["lon", "lat"],
            get_fill_color=lambda row: [
                int(row["temperature"] * 2.55),
                50,
                255 - int(row["temperature"] * 2.55),
                200,
            ],
            get_radius=1,
            radius_min_pixels=4,
            radius_max_pixels=15,
            opacity=0.9,
        ).to_spec()
    ]
    return


if __name__ == "__main__":
    app.run()
