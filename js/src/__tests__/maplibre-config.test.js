import { describe, expect, it } from "vitest";
import { applyConfigExtras, resolveStyle } from "../maplibre-config.js";

const FALLBACK = { version: 8, sources: {}, layers: [] };

function fakeMap() {
  const sources = new Map();
  const layers = new Map();
  return {
    sources,
    layers,
    getSource: (id) => sources.get(id),
    addSource: (id, spec) => sources.set(id, spec),
    getLayer: (id) => layers.get(id),
    addLayer: (spec) => layers.set(spec.id, spec),
  };
}

describe("resolveStyle", () => {
  it("prefers a config's style over basemap_style", () => {
    expect(resolveStyle({ style: "https://cfg" }, "https://plain", FALLBACK)).toBe("https://cfg");
  });

  it("falls back to basemap_style, then the fallback", () => {
    expect(resolveStyle({}, "https://plain", FALLBACK)).toBe("https://plain");
    expect(resolveStyle(null, "", FALLBACK)).toBe(FALLBACK);
  });

  it("passes inline style objects through", () => {
    const inline = { version: 8, sources: {}, layers: [] };
    expect(resolveStyle({ style: inline }, "", FALLBACK)).toBe(inline);
  });
});

describe("applyConfigExtras", () => {
  const config = {
    style: "https://s",
    sources: { wms: { type: "raster", tiles: ["https://t/{z}/{x}/{y}"] } },
    mapLayers: [{ id: "wms-layer", type: "raster", source: "wms" }],
  };

  it("adds sources and layers", () => {
    const map = fakeMap();
    applyConfigExtras(map, config);
    expect(map.sources.get("wms").type).toBe("raster");
    expect(map.layers.get("wms-layer").source).toBe("wms");
  });

  it("is idempotent across repeated style loads", () => {
    const map = fakeMap();
    applyConfigExtras(map, config);
    applyConfigExtras(map, config); // second style.load
    expect(map.sources.size).toBe(1);
    expect(map.layers.size).toBe(1);
  });

  it("tolerates empty/missing config", () => {
    const map = fakeMap();
    applyConfigExtras(map, null);
    applyConfigExtras(map, {});
    expect(map.sources.size).toBe(0);
  });
});
