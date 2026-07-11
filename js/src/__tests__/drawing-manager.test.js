import { describe, expect, it } from "vitest";
import {
  ACTIVE_DRAWING_MODES,
  DRAG_DRAW_MODES,
  deleteFeatures,
  getCursorForMode,
  getModeInstance,
} from "../drawing-manager.js";

describe("getModeInstance", () => {
  it("resolves every documented mode", () => {
    for (const mode of [
      "view", "modify", "translate", "delete",
      "draw_point", "draw_line", "draw_polygon",
      "draw_rectangle", "draw_square", "draw_circle",
    ]) {
      expect(getModeInstance(mode), mode).toBeTruthy();
    }
  });

  it("returns null for unknown modes", () => {
    expect(getModeInstance("scribble")).toBeNull();
  });
});

describe("getCursorForMode", () => {
  it("crosshair while drawing, pointer for edit/delete, grab otherwise", () => {
    expect(getCursorForMode("draw_polygon")).toBe("crosshair");
    expect(getCursorForMode("modify")).toBe("pointer");
    expect(getCursorForMode("delete")).toBe("pointer");
    expect(getCursorForMode("view")).toBe("grab");
  });
});

describe("mode sets", () => {
  it("drag-draw modes are a subset of active modes", () => {
    for (const mode of DRAG_DRAW_MODES) {
      expect(ACTIVE_DRAWING_MODES.has(mode)).toBe(true);
    }
  });
});

describe("deleteFeatures", () => {
  const fc = {
    type: "FeatureCollection",
    features: [{ id: "a" }, { id: "b" }, { id: "c" }],
  };

  it("removes features by index without mutating the input", () => {
    const out = deleteFeatures(fc, [0, 2]);
    expect(out.features.map((f) => f.id)).toEqual(["b"]);
    expect(fc.features).toHaveLength(3);
  });

  it("handles empty index lists", () => {
    expect(deleteFeatures(fc, []).features).toHaveLength(3);
  });
});
