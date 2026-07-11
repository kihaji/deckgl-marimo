# Binary Data Transfer Optimization Research

## Context

When rendering 1M polygons via the binary data path in deckgl-marimo, the Python-side packing is fast (~223ms) and GPU rendering is smooth (120 FPS), but there's a noticeable UI hitch during initial load. The bottleneck is transferring a 72.5MB binary payload from Python to the browser through anywidget's traitlet sync mechanism.

### Current Pipeline

```
numpy arrays (.tobytes()) → traitlets.Bytes → anywidget sync → WebSocket → JS DataView → ArrayBuffer copy → typed array views → deck.gl GPU upload
```

### Measured Performance (1M polygons)

| Step | Time |
|------|------|
| File load (.npz) | 200 ms |
| Binary packing (.tobytes()) | 223 ms |
| **Transfer + JS processing** | **~500-1000ms (the hitch)** |
| GPU rendering | 8.33 ms/frame (120 FPS) |

---

## How anywidget Transfers Binary Data

- `traitlets.Bytes` is the correct type — anywidget automatically uses the Jupyter widget binary buffer protocol
- Binary data bypasses JSON serialization entirely; Python `bytes` arrive as JS `DataView`
- No base64 encoding — this is already the optimal traitlet type
- The `DataView` may share an underlying `ArrayBuffer` with a non-zero `byteOffset` (anywidget implementation detail), requiring a copy to a standalone buffer before creating typed array views

### Relevant Code (current)

```javascript
// js/src/index.js — handling DataView from anywidget
if (binaryData instanceof DataView) {
  const src = new Uint8Array(binaryData.buffer, binaryData.byteOffset, binaryData.byteLength);
  const copy = new ArrayBuffer(binaryData.byteLength);
  new Uint8Array(copy).set(src);  // ~80-150ms for 72MB
  buffer = copy;
}
```

---

## How marimo Handles Widget Communication

- All Python ↔ JS communication goes over a single WebSocket connection
- No special handling for large binary payloads — the entire 72MB is sent as one WebSocket message
- marimo hooks anywidgets into its reactive execution engine, syncing traitlet changes
- Known issue: [marimo#2506](https://github.com/marimo-team/marimo/issues/2506) — binary data from file reads sometimes fails to transmit correctly (numpy array bytes work fine)

---

## Root Cause of the UI Hitch

The hitch is caused by several blocking operations on the browser's main thread:

1. **WebSocket message processing** — browser receives and buffers the entire 72MB frame before exposing it to JS
2. **ArrayBuffer copy** — copying from shared DataView buffer to standalone ArrayBuffer (~80-150ms)
3. **Typed array construction** — creating Float32Array/Uint32Array views (~50ms)
4. **deck.gl layer initialization** — GPU buffer upload for 6M vertices (~100-300ms)

All of this happens synchronously on the main thread. The browser cannot paint, respond to input, or animate during this time.

---

## Optimization Options

### 1. Chunked Transfer (Highest Priority)

**Problem:** One 72MB message blocks the browser event loop.

**Solution:** Split the binary payload into ~5MB chunks, sending each as a separate traitlet update. The browser can process UI events between chunks.

**Python side:**
```python
CHUNK_SIZE = 5 * 1024 * 1024  # 5MB

def send_chunked(widget, metadata, buffer):
    n_chunks = math.ceil(len(buffer) / CHUNK_SIZE)
    widget.binary_metadata = {
        **metadata,
        "chunked": True,
        "totalSize": len(buffer),
        "chunkCount": n_chunks,
    }
    for i in range(n_chunks):
        start = i * CHUNK_SIZE
        chunk = buffer[start:start + CHUNK_SIZE]
        widget.binary_chunk_index = i
        widget.binary_data = chunk
```

**JS side:**
```javascript
let chunks = [];
let expectedChunks = 0;

model.on("change:binary_data", () => {
  const meta = model.get("binary_metadata");
  if (!meta.chunked) {
    // Non-chunked path (existing code)
    return;
  }

  const chunkIndex = model.get("binary_chunk_index");
  const data = model.get("binary_data");
  chunks[chunkIndex] = data;
  expectedChunks = meta.chunkCount;

  if (chunks.filter(Boolean).length === expectedChunks) {
    // Reassemble
    const totalSize = meta.totalSize;
    const buffer = new ArrayBuffer(totalSize);
    const view = new Uint8Array(buffer);
    let offset = 0;
    for (const chunk of chunks) {
      const src = new Uint8Array(chunk.buffer, chunk.byteOffset, chunk.byteLength);
      view.set(src, offset);
      offset += src.byteLength;
    }
    chunks = [];
    // Process complete buffer
    applyBinaryData(specs, buffer, meta);
  }
});
```

**Expected impact:** Eliminates UI freeze. Instead of a single ~1s hitch, the load spreads across ~15 chunks with the browser responsive between each.

**Trade-offs:**
- Slightly more total transfer time due to traitlet sync overhead per chunk
- More complex state management on JS side
- Need to handle partial state (some chunks arrived, not all)

**Where to implement:** Changes needed in anywidget/marimo, or in deckgl-marimo's Map widget and JS entry point.

---

### 2. Compression (Medium Priority)

**Problem:** 72MB over WebSocket is slow regardless of chunking.

**Solution:** Compress the binary payload before sending. Polygon coordinate data has good compressibility (~3-5x with zstd).

**Python side:**
```python
import zstandard as zstd

cctx = zstd.ZstdCompressor(level=3)  # fast compression
compressed = cctx.compress(buffer)  # 72MB → ~15-20MB
widget.binary_metadata = {**metadata, "compressed": "zstd", "originalSize": len(buffer)}
widget.binary_data = compressed
```

**JS side (using fzstd — lightweight, no WASM):**
```javascript
import { decompress } from 'fzstd';

if (meta.compressed === "zstd") {
  const decompressed = decompress(new Uint8Array(buffer));
  buffer = decompressed.buffer;
}
```

**Expected impact:**
- Wire transfer: 72MB → ~15-20MB (3.5-5x reduction)
- Compression: ~50-100ms on Python side
- Decompression: ~50-100ms on JS side
- Net win if transfer time savings > compression + decompression overhead

**Trade-offs:**
- Additional dependency: `zstandard` (Python), `fzstd` (JS)
- CPU cost on both sides
- Combines well with chunking (compress, then chunk)

**Where to implement:** deckgl-marimo's `_binary.py` and JS entry point. No changes needed in anywidget/marimo.

---

### 3. HTTP Static File Serving (Alternative for Pre-generated Data)

**Problem:** The WebSocket comm channel isn't designed for bulk data transfer.

**Solution:** Instead of sending binary data through the traitlet, write it to a temporary file and serve it via marimo's HTTP server. JS fetches it directly.

**Python side:**
```python
import tempfile

# Write binary to temp file
tmp = tempfile.NamedTemporaryFile(suffix=".bin", delete=False)
tmp.write(buffer)
tmp.close()

# marimo can serve files from its working directory
# or use a custom endpoint
widget.binary_metadata = {
    **metadata,
    "method": "fetch",
    "url": f"/files/{tmp.name}",  # depends on marimo's file serving
}
```

**JS side:**
```javascript
if (meta.method === "fetch") {
  const response = await fetch(meta.url);
  const buffer = await response.arrayBuffer();
  applyBinaryData(specs, buffer, meta);
}
```

**Expected impact:**
- HTTP supports streaming, range requests, and browser caching
- No WebSocket congestion — other widget updates continue flowing
- Browser can show download progress
- Best for large static/semi-static datasets

**Trade-offs:**
- Only works for data that doesn't change reactively (or changes infrequently)
- Requires understanding marimo's file serving mechanism
- Temp file cleanup needed
- May not work in all deployment scenarios (e.g., remote marimo sessions)

**Where to investigate:** marimo's static file serving API, how `mo.download()` works internally.

---

### 4. SharedArrayBuffer (Not Recommended)

- Requires cross-origin isolation headers (`Cross-Origin-Opener-Policy`, `Cross-Origin-Embedder-Policy`)
- marimo would need to set these headers on its HTTP server
- Complex synchronization between Python/JS
- Not worth the complexity for this use case

### 5. Web Workers for Processing (Supplementary)

**Problem:** Even after receiving data, typed array construction and deck.gl initialization block the main thread.

**Solution:** Process the binary buffer in a Web Worker, then transfer the resulting typed arrays back via `postMessage` with transferable objects (zero-copy).

```javascript
// worker.js
self.onmessage = ({ data: { buffer, metadata } }) => {
  const startIndices = new Uint32Array(buffer, meta.startIndices.offset, ...);
  const coords = new Float32Array(buffer, meta.getPolygon.offset, ...);
  const colors = new Uint8Array(buffer, meta.getFillColor.offset, ...);

  // Transfer ownership back to main thread (zero-copy)
  self.postMessage(
    { startIndices, coords, colors },
    [startIndices.buffer, coords.buffer, colors.buffer]
  );
};
```

**Expected impact:** Moves ~100-200ms of typed array construction off the main thread. The GPU upload still happens on main thread (WebGL requirement).

**Where to implement:** deckgl-marimo's JS bundle. No changes needed in anywidget/marimo.

---

## Recommended Priority

| # | Optimization | Impact | Effort | Dependencies |
|---|-------------|--------|--------|-------------|
| 1 | **Chunking** | High — eliminates UI freeze | Medium | None (pure deckgl-marimo change) |
| 2 | **Compression** | Medium — reduces transfer time | Low | zstandard (Python), fzstd (JS) |
| 3 | **HTTP serving** | High for static data | Medium | Investigate marimo file serving |
| 4 | **Web Worker** | Low-medium — offloads CPU work | Medium | None |

Chunking + compression together would reduce a 72MB single-message hitch to ~15 progressive 1MB chunks — effectively invisible loading.

---

## Questions to Research Further

1. **marimo file serving:** Does marimo expose a way to serve arbitrary files to the frontend? How does `mo.download()` work internally? Could we piggyback on that for binary data?
2. **anywidget binary buffer protocol:** Is there a way to use `send()` (one-shot message) instead of trait sync for binary data? The Jupyter protocol distinguishes between state sync and custom messages.
3. **WebSocket compression:** Does marimo enable `permessage-deflate` on its WebSocket? If so, our binary data may already be compressed in transit (though less efficiently than zstd).
4. **marimo's reactivity and traitlet batching:** When we set `binary_metadata` and `binary_data` in sequence, does marimo batch these into one WebSocket message or send two? If two, the order matters (metadata must arrive before or with data).
