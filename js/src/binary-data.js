/**
 * Binary attribute reconstruction: applies Python-packed typed-array data
 * to layer specs using deck.gl's native `data.attributes` format.
 *
 * Deliberately free of deck.gl imports so it stays unit-testable in Node.
 */

export const DTYPE_CONSTRUCTORS = {
  float32: Float32Array,
  float64: Float64Array,
  uint8: Uint8Array,
  uint16: Uint16Array,
  uint32: Uint32Array,
  int8: Int8Array,
  int16: Int16Array,
  int32: Int32Array,
};

/**
 * Apply binary data to layer specs from a packed ArrayBuffer.
 *
 * @param {Array<Object>} specs - Layer specifications
 * @param {ArrayBuffer} buffer - Packed binary buffer
 * @param {Object} metadata - Describes layout: {layers: [{id, length, startIndices, attributes}]}
 */
export function applyBinaryData(specs, buffer, metadata) {
  if (!metadata || !metadata.layers || !buffer || buffer.byteLength === 0) return;

  const metaByLayer = {};
  for (const lm of metadata.layers) {
    metaByLayer[lm.id] = lm;
  }

  for (const spec of specs) {
    const lm = metaByLayer[spec.id];
    if (!lm) continue;

    // Build startIndices typed array (only for variable-length layers like Polygon/Path)
    let startIndices = undefined;
    if (lm.startIndices) {
      const SICtor = DTYPE_CONSTRUCTORS[lm.startIndices.dtype];
      startIndices = new SICtor(
        buffer,
        lm.startIndices.offset,
        lm.startIndices.byteLength / SICtor.BYTES_PER_ELEMENT
      );
    }

    // Build attribute typed arrays
    const attributes = {};
    for (const [name, meta] of Object.entries(lm.attributes)) {
      const Ctor = DTYPE_CONSTRUCTORS[meta.dtype];
      attributes[name] = {
        value: new Ctor(buffer, meta.offset, meta.byteLength / Ctor.BYTES_PER_ELEMENT),
        size: meta.size,
      };
    }

    spec.data = {
      length: lm.length,
      attributes,
    };
    if (startIndices) {
      spec.data.startIndices = startIndices;
    }
    // Forward pre-packed tooltip strings for binary-mode tooltip lookup
    if (lm.tooltips) {
      spec._tooltips = lm.tooltips;
    }
    // Mark as binary so createLayer skips accessor resolution
    spec._binary = true;
  }
}
