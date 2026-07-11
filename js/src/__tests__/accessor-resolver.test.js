import { describe, expect, it } from "vitest";
import { resolveAccessors } from "../accessor-resolver.js";

const data = [
  { lon: 1, lat: 2, size: 10, name: "a" },
  { lon: 3, lat: 4, size: 20, name: "b" },
];

describe("resolveAccessors", () => {
  it("converts a column-name string into a row accessor", () => {
    const props = { getRadius: "size", data };
    resolveAccessors(props, data);
    expect(typeof props.getRadius).toBe("function");
    expect(props.getRadius(data[1])).toBe(20);
  });

  it("leaves non-column strings as constants (e.g. TextLayer anchors)", () => {
    const props = { getTextAnchor: "middle", data };
    resolveAccessors(props, data);
    expect(props.getTextAnchor).toBe("middle");
  });

  it("converts a column-name list into a vector accessor", () => {
    const props = { getPosition: ["lon", "lat"], data };
    resolveAccessors(props, data);
    expect(props.getPosition(data[0])).toEqual([1, 2]);
  });

  it("passes small numeric arrays through as RGBA constants", () => {
    const props = { getFillColor: [255, 0, 0, 255], data };
    resolveAccessors(props, data);
    expect(props.getFillColor).toEqual([255, 0, 0, 255]);
  });

  it("converts a per-row array matching data length into an indexed accessor", () => {
    const perRow = [
      [255, 0, 0, 255],
      [0, 255, 0, 255],
    ];
    const props = { getFillColor: perRow, data };
    resolveAccessors(props, data);
    expect(typeof props.getFillColor).toBe("function");
    expect(props.getFillColor(null, { index: 1 })).toEqual([0, 255, 0, 255]);
  });

  it("only touches get* accessor props", () => {
    const props = { radiusScale: 5, stroked: true, data };
    resolveAccessors(props, data);
    expect(props.radiusScale).toBe(5);
    expect(props.stroked).toBe(true);
  });

  it("leaves existing functions alone", () => {
    const fn = (d) => d.size * 2;
    const props = { getRadius: fn, data };
    resolveAccessors(props, data);
    expect(props.getRadius).toBe(fn);
  });
});
