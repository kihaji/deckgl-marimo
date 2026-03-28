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
  const { type, ...props } = spec;

  const LayerClass = LAYER_REGISTRY[type];
  if (!LayerClass) {
    console.warn(`Unknown layer type: ${type}. Skipping.`);
    return null;
  }

  // Resolve accessor specs (get* properties) to JS functions
  resolveAccessors(props, props.data);

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
