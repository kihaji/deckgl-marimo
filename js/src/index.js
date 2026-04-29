/**
 * deckgl-marimo anywidget entry point.
 *
 * Renders a MapLibre GL map with deck.gl layers via MapboxOverlay.
 * Communicates bidirectionally with Python via anywidget model traitlets.
 */
import maplibregl from "maplibre-gl";
import maplibreCss from "maplibre-gl/dist/maplibre-gl.css";
import { MapboxOverlay } from "@deck.gl/mapbox";
import { createLayers, applyBinaryData } from "./layer-factory.js";

/**
 * Inject MapLibre CSS into the document if not already present.
 */
function ensureMaplibreCss() {
  const id = "deckgl-marimo-maplibre-css";
  if (document.getElementById(id)) return;
  const style = document.createElement("style");
  style.id = id;
  style.textContent = maplibreCss;
  document.head.appendChild(style);
}

/**
 * FPS / performance metrics tracker.
 * Uses requestAnimationFrame to measure frame times and periodically
 * pushes metrics back to the Python model.
 */
function createPerfTracker(model) {
  const frameTimes = [];
  const maxSamples = 60;
  let lastTime = performance.now();
  let lastPush = 0;
  let animId = null;
  let deckRef = null; // set externally to access deck.metrics

  function tick(now) {
    const dt = now - lastTime;
    lastTime = now;
    frameTimes.push(dt);
    if (frameTimes.length > maxSamples) frameTimes.shift();

    // Push metrics to Python every 500ms
    if (now - lastPush > 500 && frameTimes.length > 5) {
      lastPush = now;
      const avg = frameTimes.reduce((a, b) => a + b, 0) / frameTimes.length;
      const fps = 1000 / avg;
      const min = Math.min(...frameTimes);
      const max = Math.max(...frameTimes);

      const metrics = {
        fps: Math.round(fps * 10) / 10,
        frameTimeAvg: Math.round(avg * 100) / 100,
        frameTimeMin: Math.round(min * 100) / 100,
        frameTimeMax: Math.round(max * 100) / 100,
      };

      // Try to get deck.gl internal metrics
      try {
        const dm = deckRef?.metrics;
        if (dm) {
          metrics.gpuTime = dm.gpuTime;
          metrics.cpuTime = dm.cpuTime;
          metrics.gpuTimePerFrame = dm.gpuTimePerFrame;
          metrics.cpuTimePerFrame = dm.cpuTimePerFrame;
          metrics.bufferMemory = dm.bufferMemory;
          metrics.textureMemory = dm.textureMemory;
        }
      } catch (e) {
        // deck metrics not available
      }

      model.set("perf_metrics", metrics);
      model.save_changes();
    }

    animId = requestAnimationFrame(tick);
  }

  return {
    start() { animId = requestAnimationFrame(tick); },
    stop() { if (animId) cancelAnimationFrame(animId); },
    setDeck(d) { deckRef = d; },
  };
}

/**
 * Fold min/max zoom gating into each spec's `visible` prop.
 *
 * Preserves the user-supplied visible by stashing it once on `_userVisible`,
 * so repeated calls with a changing zoom are idempotent.
 */
function applyZoomVisibility(specs, zoom) {
  for (const spec of specs) {
    const hasMin = spec.minZoom != null;
    const hasMax = spec.maxZoom != null;
    if (!hasMin && !hasMax) continue;
    if (spec._userVisible === undefined) {
      spec._userVisible = spec.visible !== false;
    }
    const inRange =
      (!hasMin || zoom >= spec.minZoom) &&
      (!hasMax || zoom <= spec.maxZoom);
    spec.visible = spec._userVisible && inRange;
  }
}

/**
 * Build layers from specs, applying binary data if available.
 */
function buildLayers(model, map) {
  const specs = model.get("layer_specs") || [];
  const binaryMeta = model.get("binary_metadata") || {};
  const binaryData = model.get("binary_data");

  // anywidget delivers Bytes traitlets as DataView.
  // The underlying ArrayBuffer may be shared with a non-zero byteOffset,
  // so we must copy the relevant slice into a standalone ArrayBuffer
  // to ensure typed array constructors get correct offsets.
  let buffer = null;
  if (binaryData && binaryMeta.layers) {
    if (binaryData instanceof DataView) {
      const src = new Uint8Array(binaryData.buffer, binaryData.byteOffset, binaryData.byteLength);
      const copy = new ArrayBuffer(binaryData.byteLength);
      new Uint8Array(copy).set(src);
      buffer = copy;
    } else if (binaryData instanceof ArrayBuffer) {
      buffer = binaryData;
    } else if (binaryData && binaryData.buffer instanceof ArrayBuffer) {
      const src = new Uint8Array(binaryData.buffer, binaryData.byteOffset || 0, binaryData.byteLength);
      const copy = new ArrayBuffer(binaryData.byteLength);
      new Uint8Array(copy).set(src);
      buffer = copy;
    }
  }

  if (buffer && binaryMeta.layers) {
    applyBinaryData(specs, buffer, binaryMeta);
  }

  if (map) {
    applyZoomVisibility(specs, map.getZoom());
  }

  return createLayers(specs);
}

/**
 * anywidget render function.
 */
async function render({ model, el }) {
  ensureMaplibreCss();

  // --- Container ---
  const container = document.createElement("div");
  container.style.width = model.get("width") || "100%";
  container.style.height = model.get("height") || "600px";
  container.classList.add("deckgl-marimo-container");
  el.appendChild(container);

  // --- Performance tracker ---
  const perf = createPerfTracker(model);
  perf.start();

  // --- MapLibre Map ---
  const map = new maplibregl.Map({
    container,
    style: model.get("basemap_style") || {
      version: 8,
      sources: {},
      layers: [{ id: "background", type: "background", paint: { "background-color": "#111" } }],
    },
    center: [model.get("longitude") || 0, model.get("latitude") || 0],
    zoom: model.get("zoom") || 1,
    pitch: model.get("pitch") || 0,
    bearing: model.get("bearing") || 0,
    canvasContextAttributes: { antialias: true },
  });

  map.addControl(new maplibregl.NavigationControl(), "top-right");

  // --- deck.gl Overlay ---
  const overlay = new MapboxOverlay({
    layers: buildLayers(model, map),
    getTooltip: (info) => {
      if (!info || !info.picked || !info.layer) return null;
      // Binary layers: look up pre-packed tooltip string by feature index
      const specs = model.get("layer_specs") || [];
      const spec = specs.find((s) => s.id === info.layer.id);
      if (spec && spec._tooltips && info.index >= 0) {
        return spec._tooltips[info.index] ?? null;
      }
      // Object-based layers: read tooltip off the picked row
      return info.object ? info.object.tooltip || null : null;
    },
  });
  map.addControl(overlay);

  // Try to get the internal deck instance for metrics
  try {
    const deckInstance = overlay._deck;
    if (deckInstance) perf.setDeck(deckInstance);
  } catch (e) {
    // _deck is private, may not be accessible
  }

  // --- Reactivity: layer_specs or binary_data changes ---
  let lastZoomVisibilityKey = "";
  const rebuildLayers = () => {
    lastZoomVisibilityKey = "";  // force re-evaluation against fresh specs
    overlay.setProps({ layers: buildLayers(model, map) });
  };
  model.on("change:layer_specs", rebuildLayers);
  model.on("change:binary_data", rebuildLayers);
  model.on("change:binary_metadata", rebuildLayers);

  // --- Reactivity: zoom-based layer visibility ---
  // Fires every animation frame during zoom; we only call setProps when at
  // least one gated layer's effective visibility actually flips.
  map.on("zoom", () => {
    const specs = model.get("layer_specs") || [];
    const zoom = map.getZoom();
    let hasGated = false;
    let key = "";
    for (const s of specs) {
      if (s.minZoom == null && s.maxZoom == null) continue;
      hasGated = true;
      const inRange =
        (s.minZoom == null || zoom >= s.minZoom) &&
        (s.maxZoom == null || zoom <= s.maxZoom);
      key += `${s.id}:${inRange ? 1 : 0}|`;
    }
    if (!hasGated) return;
    if (key !== lastZoomVisibilityKey) {
      lastZoomVisibilityKey = key;
      overlay.setProps({ layers: buildLayers(model, map) });
    }
  });

  // --- Reactivity: basemap_style changes ---
  model.on("change:basemap_style", () => {
    const style = model.get("basemap_style");
    if (style) map.setStyle(style);
  });

  // --- Reactivity: layout changes ---
  model.on("change:height", () => {
    container.style.height = model.get("height");
    map.resize();
  });
  model.on("change:width", () => {
    container.style.width = model.get("width");
    map.resize();
  });

  // --- Reactivity: view state changes from Python ---
  const viewProps = ["longitude", "latitude", "zoom", "pitch", "bearing"];
  for (const prop of viewProps) {
    model.on(`change:${prop}`, () => {
      map.jumpTo({
        center: [model.get("longitude"), model.get("latitude")],
        zoom: model.get("zoom"),
        pitch: model.get("pitch"),
        bearing: model.get("bearing"),
      });
    });
  }

  // --- Viewport readback: JS -> Python ---
  map.on("moveend", () => {
    const center = map.getCenter();
    model.set("viewport", {
      longitude: center.lng,
      latitude: center.lat,
      zoom: map.getZoom(),
      pitch: map.getPitch(),
      bearing: map.getBearing(),
    });
    model.save_changes();
  });

  // --- Click/hover event readback ---
  // Gate on info.picked (deck.gl's canonical "something was picked" flag) so
  // binary-packed layers emit events too — they don't populate info.object.
  const pickPayload = (info) => ({
    object: info.object ?? null,
    coordinate: info.coordinate,
    layer_id: info.layer ? info.layer.id : null,
    index: info.index,
  });
  overlay.setProps({
    ...overlay.props,
    onClick: (info) => {
      if (info && info.picked) {
        model.set("click_info", pickPayload(info));
        model.save_changes();
      }
    },
    onHover: (info) => {
      if (info && info.picked) {
        model.set("hover_info", pickPayload(info));
        model.save_changes();
      }
    },
  });

  // --- Cleanup ---
  return () => {
    perf.stop();
    overlay.finalize();
    map.remove();
  };
}

export default { render };
