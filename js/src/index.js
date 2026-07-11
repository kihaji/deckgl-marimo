/**
 * deckgl-marimo anywidget entry point.
 *
 * Renders a MapLibre GL map with deck.gl layers via MapboxOverlay.
 * Communicates bidirectionally with Python via anywidget model traitlets.
 */
import maplibregl from "maplibre-gl";
import maplibreCss from "maplibre-gl/dist/maplibre-gl.css";
import { MapboxOverlay } from "@deck.gl/mapbox";
import { createLayers } from "./layer-factory.js";
import { applyBinaryData } from "./binary-data.js";
import { normalizeBinaryBuffer } from "./binary-buffer.js";
import { applyZoomVisibility, zoomVisibilityKey } from "./zoom-visibility.js";
import { createPerfTracker } from "./perf-tracker.js";
import { attachPickHandlers } from "./pick-events.js";

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
 * Build layers from specs, applying binary data if available.
 */
function buildLayers(model, map) {
  const specs = model.get("layer_specs") || [];
  const binaryMeta = model.get("binary_metadata") || {};
  const binaryData = model.get("binary_data");

  const buffer = binaryMeta.layers ? normalizeBinaryBuffer(binaryData) : null;
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

  // --- Performance tracker (opt-in: show_perf_metrics) ---
  const perf = createPerfTracker(model);
  const syncPerfTracker = () => {
    if (model.get("show_perf_metrics")) {
      perf.start();
    } else {
      perf.stop();
    }
  };
  model.on("change:show_perf_metrics", syncPerfTracker);
  syncPerfTracker();

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
    const key = zoomVisibilityKey(model.get("layer_specs") || [], map.getZoom());
    if (key === null) return;
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

  // --- Fit-bounds requests from Python ---
  const applyFitBounds = () => {
    const req = model.get("fit_bounds_request");
    if (req && req.bounds) {
      map.fitBounds(req.bounds, { padding: req.padding ?? 20 });
    }
  };
  model.on("change:fit_bounds_request", applyFitBounds);
  applyFitBounds(); // honor a request made before first render

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
  attachPickHandlers(overlay, model);

  // --- Cleanup ---
  return () => {
    perf.stop();
    overlay.finalize();
    map.remove();
  };
}

export default { render };
