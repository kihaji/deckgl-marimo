import { describe, expect, it } from "vitest";
import { applyBinaryData } from "../binary-data.js";

/**
 * Build a packed buffer the way Python's pack_binary does: startIndices
 * first (4-byte aligned), then each attribute aligned to its dtype.
 */
function packFixture() {
  // Layer "pts": 2 points, positions float32 x2, colors uint8 x4
  const positions = new Float32Array([10.5, 20.5, -30.25, 40.75]); // 16 bytes @ 0
  const colors = new Uint8Array([255, 0, 0, 255, 0, 255, 0, 128]); // 8 bytes @ 16
  const buffer = new ArrayBuffer(24);
  new Uint8Array(buffer).set(new Uint8Array(positions.buffer), 0);
  new Uint8Array(buffer).set(colors, 16);

  const metadata = {
    layers: [
      {
        id: "pts",
        length: 2,
        attributes: {
          getPosition: { offset: 0, byteLength: 16, dtype: "float32", size: 2 },
          getFillColor: { offset: 16, byteLength: 8, dtype: "uint8", size: 4 },
        },
        tooltips: ["first", "second"],
      },
    ],
  };
  return { buffer, metadata };
}

describe("applyBinaryData", () => {
  it("reconstructs typed arrays with correct offsets, values, and sizes", () => {
    const { buffer, metadata } = packFixture();
    const specs = [{ id: "pts", type: "ScatterplotLayer" }];
    applyBinaryData(specs, buffer, metadata);

    const spec = specs[0];
    expect(spec._binary).toBe(true);
    expect(spec.data.length).toBe(2);
    expect(spec.data.attributes.getPosition.size).toBe(2);
    expect(Array.from(spec.data.attributes.getPosition.value)).toEqual([10.5, 20.5, -30.25, 40.75]);
    expect(spec.data.attributes.getFillColor.size).toBe(4);
    expect(Array.from(spec.data.attributes.getFillColor.value)).toEqual([255, 0, 0, 255, 0, 255, 0, 128]);
    expect(spec._tooltips).toEqual(["first", "second"]);
  });

  it("builds startIndices for variable-length layers", () => {
    // startIndices uint32 [0, 3] @ 0 (8 bytes), path coords float32 @ 8
    const si = new Uint32Array([0, 3]);
    const coords = new Float32Array([0, 0, 1, 1, 2, 2, 5, 5, 6, 6]); // 40 bytes
    const buffer = new ArrayBuffer(48);
    new Uint8Array(buffer).set(new Uint8Array(si.buffer), 0);
    new Uint8Array(buffer).set(new Uint8Array(coords.buffer), 8);

    const metadata = {
      layers: [
        {
          id: "paths",
          length: 2,
          startIndices: { offset: 0, byteLength: 8, dtype: "uint32" },
          attributes: {
            getPath: { offset: 8, byteLength: 40, dtype: "float32", size: 2 },
          },
        },
      ],
    };
    const specs = [{ id: "paths", type: "PathLayer" }];
    applyBinaryData(specs, buffer, metadata);

    expect(Array.from(specs[0].data.startIndices)).toEqual([0, 3]);
    expect(specs[0].data.attributes.getPath.value.length).toBe(10);
  });

  it("leaves specs without matching metadata untouched", () => {
    const { buffer, metadata } = packFixture();
    const specs = [{ id: "other", type: "ScatterplotLayer", data: [{ a: 1 }] }];
    applyBinaryData(specs, buffer, metadata);
    expect(specs[0]._binary).toBeUndefined();
    expect(specs[0].data).toEqual([{ a: 1 }]);
  });

  it("is a no-op for empty buffers or missing metadata", () => {
    const specs = [{ id: "pts" }];
    applyBinaryData(specs, new ArrayBuffer(0), { layers: [{ id: "pts", attributes: {} }] });
    applyBinaryData(specs, null, { layers: [] });
    applyBinaryData(specs, new ArrayBuffer(8), null);
    expect(specs[0].data).toBeUndefined();
  });
});
