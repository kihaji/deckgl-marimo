/**
 * Generic deck.gl layer factory.
 * Creates any deck.gl layer from a JSON spec sent from Python.
 */
import {
  ArcLayer,
  BitmapLayer,
  ColumnLayer,
  GeoJsonLayer,
  GridCellLayer,
  IconLayer,
  LineLayer,
  PathLayer,
  PointCloudLayer,
  PolygonLayer,
  ScatterplotLayer,
  SolidPolygonLayer,
  TextLayer,
} from "@deck.gl/layers";

import {
  ContourLayer,
  GridLayer,
  HeatmapLayer,
  HexagonLayer,
  ScreenGridLayer,
} from "@deck.gl/aggregation-layers";

import {
  GreatCircleLayer,
  H3ClusterLayer,
  H3HexagonLayer,
  MVTLayer,
  QuadkeyLayer,
  S2Layer,
  TerrainLayer,
  TileLayer,
  Tile3DLayer,
  TripsLayer,
} from "@deck.gl/geo-layers";

import { SimpleMeshLayer, ScenegraphLayer } from "@deck.gl/mesh-layers";

import { resolveAccessors } from "./accessor-resolver.js";

const DTYPE_CONSTRUCTORS = {
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
    // Mark as binary so createLayer skips accessor resolution
    spec._binary = true;
  }
}

/**
 * Registry mapping layer type names to deck.gl layer classes.
 */
const LAYER_REGISTRY = {
  // Core layers
  ArcLayer,
  BitmapLayer,
  ColumnLayer,
  GeoJsonLayer,
  GridCellLayer,
  IconLayer,
  LineLayer,
  PathLayer,
  PointCloudLayer,
  PolygonLayer,
  ScatterplotLayer,
  SolidPolygonLayer,
  TextLayer,

  // Aggregation layers
  ContourLayer,
  GridLayer,
  HeatmapLayer,
  HexagonLayer,
  ScreenGridLayer,

  // Geo layers
  GreatCircleLayer,
  H3ClusterLayer,
  H3HexagonLayer,
  MVTLayer,
  QuadkeyLayer,
  S2Layer,
  TerrainLayer,
  TileLayer,
  Tile3DLayer,
  TripsLayer,

  // Mesh layers
  SimpleMeshLayer,
  ScenegraphLayer,
};

/**
 * Create a deck.gl layer instance from a JSON spec.
 *
 * @param {Object} spec - Layer specification from Python's BaseLayer.to_spec()
 * @returns {Layer} A deck.gl layer instance
 */
export function createLayer(spec) {
  const { type, _binary, ...props } = spec;

  const LayerClass = LAYER_REGISTRY[type];
  if (!LayerClass) {
    console.warn(`Unknown layer type: ${type}. Skipping.`);
    return null;
  }

  // Skip accessor resolution for binary data — deck.gl handles it natively
  if (!_binary) {
    resolveAccessors(props, props.data);
  }

  return new LayerClass(props);
}

/**
 * Create multiple deck.gl layers from an array of specs.
 *
 * @param {Array<Object>} specs - Array of layer specifications
 * @returns {Array<Layer>} Array of deck.gl layer instances
 */
export function createLayers(specs) {
  return specs.map(createLayer).filter(Boolean);
}
