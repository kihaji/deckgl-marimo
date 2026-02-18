from deckgl_marimo import DeckGLHexagonWidget


def test_widget_creation():
    w = DeckGLHexagonWidget(style_url="https://example.com/style.json")
    assert w.style_url == "https://example.com/style.json"
    assert w.positions == []
    assert w.radius == 1000
    assert w.zoom == 6.0


def test_widget_with_data():
    data = [{"lat": 51.5, "lon": -0.1}]
    w = DeckGLHexagonWidget(style_url="https://example.com/style.json", data=data)
    assert w.positions == [[-0.1, 51.5]]


def test_widget_custom_columns():
    data = [{"latitude": 10.0, "longitude": 20.0}]
    w = DeckGLHexagonWidget(
        style_url="https://example.com/style.json",
        data=data,
        lat_col="latitude",
        lon_col="longitude",
    )
    assert w.positions == [[20.0, 10.0]]


def test_widget_kwargs():
    w = DeckGLHexagonWidget(
        style_url="https://example.com/style.json",
        radius=500,
        coverage=0.8,
        elevation_scale=100,
        pitch=60.0,
    )
    assert w.radius == 500
    assert w.coverage == 0.8
    assert w.elevation_scale == 100
    assert w.pitch == 60.0
