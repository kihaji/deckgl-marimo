import { describe, expect, it } from "vitest";
import { normalizeBinaryBuffer } from "../binary-buffer.js";

describe("normalizeBinaryBuffer", () => {
  it("returns null for empty input", () => {
    expect(normalizeBinaryBuffer(null)).toBeNull();
    expect(normalizeBinaryBuffer(undefined)).toBeNull();
    expect(normalizeBinaryBuffer("")).toBeNull();
  });

  it("copies a DataView slice with a non-zero byteOffset into a standalone buffer", () => {
    // Backing buffer: [0,1,2,3,4,5,6,7]; DataView covers [2..5]
    const backing = new Uint8Array([0, 1, 2, 3, 4, 5, 6, 7]).buffer;
    const view = new DataView(backing, 2, 4);
    const out = normalizeBinaryBuffer(view);
    expect(out).toBeInstanceOf(ArrayBuffer);
    expect(out).not.toBe(backing);
    expect(out.byteLength).toBe(4);
    expect(Array.from(new Uint8Array(out))).toEqual([2, 3, 4, 5]);
  });

  it("passes a bare ArrayBuffer through unchanged", () => {
    const buf = new Uint8Array([9, 8, 7]).buffer;
    expect(normalizeBinaryBuffer(buf)).toBe(buf);
  });

  it("copies a typed-array view (offset subarray) into a standalone buffer", () => {
    const backing = new Uint8Array([0, 1, 2, 3, 4, 5, 6, 7]);
    const sub = backing.subarray(3, 6); // bytes [3,4,5]
    const out = normalizeBinaryBuffer(sub);
    expect(out).toBeInstanceOf(ArrayBuffer);
    expect(Array.from(new Uint8Array(out))).toEqual([3, 4, 5]);
  });

  it("returns null for objects with no usable buffer", () => {
    expect(normalizeBinaryBuffer({ buffer: "nope" })).toBeNull();
  });
});
