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
    antialias: true,
  });

  map.addControl(new maplibregl.NavigationControl(), "top-right");

  // --- deck.gl Overlay ---
  const layerSpecs = model.get("layer_specs") || [];
  const overlay = new MapboxOverlay({
    layers: createLayers(layerSpecs),
    getTooltip: ({ object }) => object && (object.tooltip || null),
  });
  map.addControl(overlay);

  // --- Reactivity: layer_specs changes ---
  model.on("change:layer_specs", () => {
    const specs = model.get("layer_specs") || [];
    overlay.setProps({ layers: createLayers(specs) });
  });

  // --- Reactivity: basemap_style changes ---
  model.on("change:basemap_style", () => {
    const style = model.get("basemap_style");
    if (style) {
      map.setStyle(style);
    }
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
      const lng = model.get("longitude");
      const lat = model.get("latitude");
      map.jumpTo({
        center: [lng, lat],
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

  // --- Click event readback ---
  overlay.setProps({
    ...overlay.props,
    onClick: (info) => {
      if (info && info.object) {
        model.set("click_info", {
          object: info.object,
          coordinate: info.coordinate,
          layer_id: info.layer ? info.layer.id : null,
          index: info.index,
        });
        model.save_changes();
      }
    },
    onHover: (info) => {
      if (info && info.object) {
        model.set("hover_info", {
          object: info.object,
          coordinate: info.coordinate,
          layer_id: info.layer ? info.layer.id : null,
          index: info.index,
        });
        model.save_changes();
      }
    },
  });

  // --- Cleanup ---
  return () => {
    overlay.finalize();
    map.remove();
  };
}

export default { render };
