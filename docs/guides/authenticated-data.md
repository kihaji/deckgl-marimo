# Authenticated Data

Layers that load data from URLs fetch it in the browser via deck.gl's
loaders.gl. Two escape hatches control that request — available on every
layer:

## `fetch_headers` — the common case

```python
# Bearer token
dgl.GeoJsonLayer(
    data="https://secure-api.example.com/data.geojson",
    fetch_headers={"Authorization": "Bearer my-token"},
)

# API key header
dgl.GeoJsonLayer(
    data="https://api.example.com/features",
    fetch_headers={"X-API-Key": "abc123"},
)
```

## `load_options` — full fetch control

Anything loaders.gl accepts, e.g. cookies/mTLS via `credentials`, CORS
modes, or combined headers:

```python
dgl.GeoJsonLayer(
    data="https://internal.example.com/data.geojson",
    load_options={
        "fetch": {
            "credentials": "include",
            "mode": "cors",
            "headers": {"Authorization": "Bearer token"},
        }
    },
)
```

When both specify headers, `load_options` headers win on conflicts.

!!! warning "Tokens travel to the browser"
    These values are serialized into the widget state and used by
    frontend fetches — treat them like any credential you'd put in
    client-side code, and prefer short-lived scoped tokens.
