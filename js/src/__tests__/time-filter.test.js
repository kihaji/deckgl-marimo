import { describe, expect, it } from "vitest";
import { DataFilterExtension } from "@deck.gl/extensions";
import {
  advanceHead,
  applyRangeToLayers,
  computeFilterRange,
  isFilterTarget,
  resolveHeadTime,
} from "../time-filter.js";

describe("computeFilterRange", () => {
  it("computes the hard sliding window", () => {
    expect(computeFilterRange(10, { window: 4 })).toEqual({ range: [6, 10], soft: null });
  });

  it("adds a soft fade range when softEdge is set", () => {
    expect(computeFilterRange(10, { window: 4, softEdge: 1 })).toEqual({
      range: [6, 10],
      soft: [5, 11],
    });
  });
});

describe("isFilterTarget", () => {
  it("honors an explicit layerIds allowlist", () => {
    const layer = { id: "a", props: {} };
    expect(isFilterTarget(layer, { layerIds: ["a"] })).toBe(true);
    expect(isFilterTarget(layer, { layerIds: ["b"] })).toBe(false);
  });

  it("auto-detects DataFilterExtension layers", () => {
    const withExt = { id: "x", props: { extensions: [new DataFilterExtension({ filterSize: 1 })] } };
    const without = { id: "y", props: { extensions: [] } };
    expect(isFilterTarget(withExt, {})).toBe(true);
    expect(isFilterTarget(without, {})).toBe(false);
  });
});

describe("applyRangeToLayers", () => {
  it("clones only target layers with the window range", () => {
    const cloned = [];
    const target = {
      id: "t",
      props: { extensions: [new DataFilterExtension({ filterSize: 1 })] },
      clone(overrides) {
        cloned.push(overrides);
        return { ...this, ...overrides };
      },
    };
    const bystander = { id: "b", props: {} };
    const result = applyRangeToLayers([target, bystander], 10, { window: 4 });
    expect(cloned).toEqual([{ filterRange: [6, 10] }]);
    expect(result[1]).toBe(bystander);
  });
});

describe("resolveHeadTime", () => {
  it("paused: the incoming current is authoritative", () => {
    expect(resolveHeadTime({ playing: false, current: 7 }, 3)).toBe(7);
  });

  it("playing: keeps the live head", () => {
    expect(resolveHeadTime({ playing: true, current: 7 }, 3)).toBe(3);
  });

  it("seeds from current, then domain start + window", () => {
    expect(resolveHeadTime({ playing: true, current: 7 }, null)).toBe(7);
    expect(resolveHeadTime({ playing: true, domain: [5, 20], window: 2 }, null)).toBe(7);
  });
});

describe("advanceHead", () => {
  const tf = { domain: [0, 10], window: 2, speed: 4, loop: true };

  it("advances by speed * dt", () => {
    expect(advanceHead(3, 0.5, tf)).toBe(5);
  });

  it("loops back into the window range at the end", () => {
    // start = 2, end = 10, span = 8; 9 + 4*0.5 = 11 -> 2 + (11-2)%8 = 3
    expect(advanceHead(9, 0.5, tf)).toBe(3);
  });

  it("clamps at the end when loop is false", () => {
    expect(advanceHead(9, 1, { ...tf, loop: false })).toBe(10);
  });

  it("defaults speed to a ~20s sweep", () => {
    expect(advanceHead(2, 1, { domain: [0, 10], window: 2 })).toBe(2.5);
  });
});
