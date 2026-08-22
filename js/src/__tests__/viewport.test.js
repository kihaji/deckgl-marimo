import { describe, expect, it } from "vitest";
import { viewportPayload } from "../viewport.js";

function fakeMap({ center = { lng: -95.5, lat: 37 }, zoom = 3.5, pitch = 0, bearing = 0, bounds } = {}) {
  return {
    getCenter: () => center,
    getZoom: () => zoom,
    getPitch: () => pitch,
    getBearing: () => bearing,
    ...(bounds
      ? {
          getBounds: () => ({
            getSouthWest: () => ({ lng: bounds[0][0], lat: bounds[0][1] }),
            getNorthEast: () => ({ lng: bounds[1][0], lat: bounds[1][1] }),
          }),
        }
      : {}),
  };
}

describe("viewportPayload", () => {
  it("reports center/zoom/pitch/bearing", () => {
    const p = viewportPayload(fakeMap({ zoom: 7.25, pitch: 40, bearing: -15 }));
    expect(p).toMatchObject({ longitude: -95.5, latitude: 37, zoom: 7.25, pitch: 40, bearing: -15 });
  });

  it("adds bounds as [[west, south], [east, north]] (lower-left, upper-right)", () => {
    const p = viewportPayload(fakeMap({ bounds: [[-110.2, 30.1], [-80.9, 44.6]] }));
    expect(p.bounds).toEqual([
      [-110.2, 30.1],
      [-80.9, 44.6],
    ]);
  });

  it("passes unwrapped antimeridian longitudes through unchanged", () => {
    const p = viewportPayload(fakeMap({ bounds: [[170, -10], [190, 10]] }));
    expect(p.bounds[1][0]).toBe(190);
  });

  it("omits bounds when the map cannot provide them", () => {
    const p = viewportPayload(fakeMap());
    expect(p).not.toHaveProperty("bounds");
  });
});
