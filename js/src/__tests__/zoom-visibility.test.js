import { describe, expect, it } from "vitest";
import { applyZoomVisibility, isInZoomRange, zoomVisibilityKey } from "../zoom-visibility.js";

describe("isInZoomRange", () => {
  it("is unbounded when neither bound is set", () => {
    expect(isInZoomRange({}, 0)).toBe(true);
    expect(isInZoomRange({}, 22)).toBe(true);
  });

  it("applies inclusive min and max bounds", () => {
    const spec = { visibleMinZoom: 5, visibleMaxZoom: 10 };
    expect(isInZoomRange(spec, 4.99)).toBe(false);
    expect(isInZoomRange(spec, 5)).toBe(true);
    expect(isInZoomRange(spec, 10)).toBe(true);
    expect(isInZoomRange(spec, 10.01)).toBe(false);
  });

  it("supports one-sided bounds", () => {
    expect(isInZoomRange({ visibleMinZoom: 8 }, 7)).toBe(false);
    expect(isInZoomRange({ visibleMinZoom: 8 }, 9)).toBe(true);
    expect(isInZoomRange({ visibleMaxZoom: 8 }, 7)).toBe(true);
    expect(isInZoomRange({ visibleMaxZoom: 8 }, 9)).toBe(false);
  });
});

describe("applyZoomVisibility", () => {
  it("leaves ungated specs untouched", () => {
    const specs = [{ id: "a", visible: true }];
    applyZoomVisibility(specs, 3);
    expect(specs[0].visible).toBe(true);
    expect(specs[0]._userVisible).toBeUndefined();
  });

  it("gates visibility by zoom range", () => {
    const specs = [{ id: "a", visible: true, visibleMinZoom: 5 }];
    applyZoomVisibility(specs, 3);
    expect(specs[0].visible).toBe(false);
    applyZoomVisibility(specs, 6);
    expect(specs[0].visible).toBe(true);
  });

  it("is idempotent: repeated calls never lose the user-supplied visible", () => {
    const specs = [{ id: "a", visible: false, visibleMinZoom: 5 }];
    applyZoomVisibility(specs, 6);
    expect(specs[0].visible).toBe(false); // user said hidden — stays hidden in range
    applyZoomVisibility(specs, 3);
    applyZoomVisibility(specs, 6);
    expect(specs[0].visible).toBe(false);
    expect(specs[0]._userVisible).toBe(false);
  });

  it("treats missing visible as true", () => {
    const specs = [{ id: "a", visibleMinZoom: 5 }];
    applyZoomVisibility(specs, 6);
    expect(specs[0].visible).toBe(true);
  });
});

describe("zoomVisibilityKey", () => {
  it("returns null when nothing is gated", () => {
    expect(zoomVisibilityKey([{ id: "a" }, { id: "b" }], 5)).toBeNull();
  });

  it("fingerprints only gated specs and changes exactly when a gate flips", () => {
    const specs = [
      { id: "a", visibleMinZoom: 5 },
      { id: "b" },
      { id: "c", visibleMaxZoom: 8 },
    ];
    const k1 = zoomVisibilityKey(specs, 6); // a in, c in
    const k2 = zoomVisibilityKey(specs, 7); // same states
    const k3 = zoomVisibilityKey(specs, 9); // c flips out
    expect(k1).toBe(k2);
    expect(k1).not.toBe(k3);
    expect(k1).toBe("a:1|c:1|");
    expect(k3).toBe("a:1|c:0|");
  });
});
