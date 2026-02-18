import maplibregl from "https://esm.sh/maplibre-gl@4.7.1";

// --- deck.gl via standalone bundle (avoids ESM packaging issues) ---
const DECKGL_VERSION = "9.1.8";
const deckReady = (() => {
  if (window.deck) return Promise.resolve(window.deck);
  return new Promise((resolve, reject) => {
    const existing = document.querySelector(
      'script[src*="deck.gl/dist.min.js"]'
    );
    if (existing) {
      existing.addEventListener("load", () => resolve(window.deck));
      return;
    }
    const script = document.createElement("script");
    script.src = `https://unpkg.com/deck.gl@${DECKGL_VERSION}/dist.min.js`;
    script.onload = () => resolve(window.deck);
    script.onerror = () => reject(new Error("Failed to load deck.gl"));
    document.head.appendChild(script);
  });
})();

// Traitlet names that map to HexagonLayer props
const LAYER_PROPS = [
  "radius",
  "elevation_scale",
  "color_range",
  "extruded",
  "coverage",
  "upper_percentile",
  "pickable",
];

function getLayerProps(model) {
  return {
    radius: model.get("radius"),
    elevationScale: model.get("elevation_scale"),
    colorRange: model.get("color_range"),
    extruded: model.get("extruded"),
    coverage: model.get("coverage"),
    upperPercentile: model.get("upper_percentile"),
    pickable: model.get("pickable"),
  };
}

function buildLayer(deck, model) {
  const positions = model.get("positions") || [];
  return new deck.HexagonLayer({
    id: "hexagon-layer",
    data: positions,
    getPosition: (d) => d,
    ...getLayerProps(model),
  });
}

async function render({ model, el }) {
  const deck = await deckReady;

  // Container
  const container = document.createElement("div");
  container.style.width = "100%";
  container.style.height = model.get("map_height");
  container.classList.add("deckgl-marimo-container");
  el.appendChild(container);

  // MapLibre map
  const map = new maplibregl.Map({
    container,
    style: model.get("style_url"),
    center: [model.get("center_lon"), model.get("center_lat")],
    zoom: model.get("zoom"),
    pitch: model.get("pitch"),
    bearing: model.get("bearing"),
    antialias: true,
  });

  map.addControl(new maplibregl.NavigationControl(), "top-right");

  // deck.gl overlay
  const overlay = new deck.MapboxOverlay({
    layers: [buildLayer(deck, model)],
  });
  map.addControl(overlay);

  // React to traitlet changes — rebuild layer
  const layerTraitlets = ["positions", ...LAYER_PROPS];
  for (const name of layerTraitlets) {
    model.on(`change:${name}`, () => {
      overlay.setProps({ layers: [buildLayer(deck, model)] });
    });
  }

  // React to map_height changes
  model.on("change:map_height", () => {
    container.style.height = model.get("map_height");
    map.resize();
  });

  // Write viewport back to Python on moveend
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

  // Cleanup
  return () => {
    overlay.finalize();
    map.remove();
  };
}

export default { render };
