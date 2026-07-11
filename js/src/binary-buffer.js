/**
 * Normalize the anywidget binary payload to a standalone ArrayBuffer.
 *
 * anywidget delivers Bytes traitlets as a DataView. The underlying
 * ArrayBuffer may be shared with a non-zero byteOffset, so the relevant
 * slice must be copied into a standalone ArrayBuffer to ensure typed array
 * constructors get correct offsets.
 *
 * @param {DataView|ArrayBuffer|{buffer: ArrayBuffer}} binaryData
 * @returns {ArrayBuffer|null} standalone buffer, or null when unusable
 */
export function normalizeBinaryBuffer(binaryData) {
  if (!binaryData) return null;
  if (binaryData instanceof DataView) {
    const src = new Uint8Array(binaryData.buffer, binaryData.byteOffset, binaryData.byteLength);
    const copy = new ArrayBuffer(binaryData.byteLength);
    new Uint8Array(copy).set(src);
    return copy;
  }
  if (binaryData instanceof ArrayBuffer) {
    return binaryData;
  }
  if (binaryData.buffer instanceof ArrayBuffer) {
    const src = new Uint8Array(binaryData.buffer, binaryData.byteOffset || 0, binaryData.byteLength);
    const copy = new ArrayBuffer(binaryData.byteLength);
    new Uint8Array(copy).set(src);
    return copy;
  }
  return null;
}
