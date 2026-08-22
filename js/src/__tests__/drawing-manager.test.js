import { describe, expect, it } from "vitest";
import {
  ACTIVE_DRAWING_MODES,
  DRAG_DRAW_MODES,
  DRAWING_LAYER_ID,
  SELECTION_MODES,
  SYNC_EVENTS,
  deleteFeatures,
  getCursorForMode,
  getModeInstance,
} from "../drawing-manager.js";
import { pickStartsEditDrag } from "../drawing.js";

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

describe("SYNC_EVENTS", () => {
  it("syncs completed edits, including translate drops, but not in-progress events", () => {
    for (const completed of [
      "addFeature", "finishMovePosition", "removePosition", "addPosition", "deleteFeature", "translated",
    ]) {
      expect(SYNC_EVENTS.has(completed), completed).toBe(true);
    }
    for (const inProgress of ["movePosition", "translating", "addTentativePosition", "updateTentativeFeature"]) {
      expect(SYNC_EVENTS.has(inProgress), inProgress).toBe(false);
    }
  });
});

describe("pickStartsEditDrag (drag-pan guard)", () => {
  const handle = { isGuide: true, index: 3, object: { properties: { guideType: "editHandle" } } };
  const feature = { isGuide: false, index: 1, object: { type: "Feature" } };

  it("edit handles start an edit drag in any selection mode", () => {
    for (const mode of SELECTION_MODES) {
      expect(pickStartsEditDrag(handle, mode, []), mode).toBe(true);
    }
  });

  it("selected features drag only in translate mode", () => {
    expect(pickStartsEditDrag(feature, "translate", [1])).toBe(true);
    expect(pickStartsEditDrag(feature, "translate", [0])).toBe(false);
    expect(pickStartsEditDrag(feature, "modify", [1])).toBe(false);
  });

  it("tolerates missing picks", () => {
    expect(pickStartsEditDrag(null, "modify", [])).toBe(false);
    expect(pickStartsEditDrag({ isGuide: true, index: 0 }, "modify", [])).toBe(false);
  });

  it("exposes the editable layer id", () => {
    expect(DRAWING_LAYER_ID).toBe("__drawing-layer");
  });
});
