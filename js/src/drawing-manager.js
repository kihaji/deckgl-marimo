/**
 * Drawing manager — creates and manages an EditableGeoJsonLayer for
 * interactive drawing, using @deck.gl-community/editable-layers.
 *
 * Ported from deckgl_dash's utils/drawingManager.js; React state setters
 * are replaced by plain callbacks.
 */

import {
  EditableGeoJsonLayer,
  ViewMode,
  ModifyMode,
  TranslateMode,
  DrawPointMode,
  DrawLineStringMode,
  DrawPolygonMode,
  DrawRectangleMode,
  DrawSquareMode,
  DrawCircleFromCenterMode,
  DeleteMode,
} from "@deck.gl-community/editable-layers";

/** Map of user-facing mode strings to editable-layers mode instances. */
const MODE_MAP = {
  view: new ViewMode(),
  modify: new ModifyMode(),
  translate: new TranslateMode(),
  draw_point: new DrawPointMode(),
  draw_line: new DrawLineStringMode(),
  draw_polygon: new DrawPolygonMode(),
  draw_rectangle: new DrawRectangleMode(),
  draw_square: new DrawSquareMode(),
  draw_circle: new DrawCircleFromCenterMode(),
  delete: new DeleteMode(),
};

/** Drawing modes that use drag interaction (conflict with map panning). */
export const DRAG_DRAW_MODES = new Set(["draw_circle", "draw_rectangle", "draw_square"]);

/** All active drawing modes (not view) — used for cursor and doubleClickZoom. */
export const ACTIVE_DRAWING_MODES = new Set([
  "draw_point", "draw_line", "draw_polygon",
  "draw_rectangle", "draw_square", "draw_circle",
]);

/** Modes where clicking a feature should select it. */
export const SELECTION_MODES = new Set(["modify", "translate"]);

/** deck.gl layer id of the editable layer (used for targeted picking). */
export const DRAWING_LAYER_ID = "__drawing-layer";

/** Edit types that should sync completed state to Python. */
export const SYNC_EVENTS = new Set([
  "addFeature", "finishMovePosition", "removePosition", "addPosition", "deleteFeature",
  "translated",
]);

/** Get the mode instance for a mode string (null when unknown). */
export function getModeInstance(modeStr) {
  return MODE_MAP[modeStr] || null;
}

const DEFAULT_STYLE = {
  fillColor: [255, 140, 0, 100],
  lineColor: [0, 0, 0, 255],
  lineWidth: 2,
  tentativeFillColor: [255, 140, 0, 50],
  tentativeLineColor: [255, 140, 0, 200],
  editHandlePointColor: [255, 0, 0, 255],
  selectedFillColor: [255, 200, 0, 150],
  selectedLineColor: [255, 100, 0, 255],
  pointRadius: 5,
};

/** CSS cursor for each drawing mode. */
export function getCursorForMode(modeStr) {
  if (ACTIVE_DRAWING_MODES.has(modeStr)) return "crosshair";
  if (SELECTION_MODES.has(modeStr) || modeStr === "delete") return "pointer";
  return "grab";
}

/**
 * Create an EditableGeoJsonLayer for drawing/editing.
 *
 * @param {object} drawingConfig - { mode, selectedFeatureIndexes, style }
 * @param {object} features - Current GeoJSON FeatureCollection
 * @param {number[]} selectedIndexes - Currently selected feature indexes
 * @param {object} callbacks - { setFeatures, setSelectedIndexes, syncToModel, onCancelPan? }
 * @returns {EditableGeoJsonLayer|null}
 */
export function createEditableLayer(drawingConfig, features, selectedIndexes, callbacks) {
  const { mode: modeStr, style = {} } = drawingConfig;
  const modeInstance = getModeInstance(modeStr);
  if (!modeInstance) {
    console.warn(`Unknown drawing mode: ${modeStr}`);
    return null;
  }

  const mergedStyle = { ...DEFAULT_STYLE, ...style };
  const isSelectionMode = SELECTION_MODES.has(modeStr);
  const { setFeatures, setSelectedIndexes, syncToModel, onCancelPan } = callbacks;

  return new EditableGeoJsonLayer({
    id: DRAWING_LAYER_ID,
    data: features,
    mode: modeInstance,
    selectedFeatureIndexes: selectedIndexes,

    // Committed feature styles — highlight selected features differently
    getFillColor: (feature, { index }) =>
      selectedIndexes.includes(index) ? mergedStyle.selectedFillColor : mergedStyle.fillColor,
    getLineColor: (feature, { index }) =>
      selectedIndexes.includes(index) ? mergedStyle.selectedLineColor : mergedStyle.lineColor,
    getLineWidth: () => mergedStyle.lineWidth,

    // Point size
    getRadius: () => mergedStyle.pointRadius,
    pointRadiusMinPixels: mergedStyle.pointRadius,
    pointRadiusUnits: "pixels",

    // Tentative (in-progress) feature styles
    getTentativeFillColor: () => mergedStyle.tentativeFillColor,
    getTentativeLineColor: () => mergedStyle.tentativeLineColor,
    getTentativeLineWidth: () => mergedStyle.lineWidth,

    // Edit handle styles
    getEditHandlePointColor: () => mergedStyle.editHandlePointColor,
    editHandlePointRadiusScale: 4,
    editHandlePointRadiusMinPixels: 4,

    // Mode config — controls measurement tooltips
    modeConfig: mergedStyle.showMeasurements === false
      ? { formatTooltip: () => null }
      : {},

    pickable: true,
    autoHighlight: false,

    // Edit modes call cancelPan() when a vertex/feature drag starts; the
    // controller uses it to suspend MapLibre's drag-pan for that gesture.
    onCancelPan: onCancelPan || undefined,

    // Click handler for selection in modify/translate modes. Guide picks
    // (edit handles) carry the handle index, not a feature index — ignore them.
    onClick: (info) => {
      if (isSelectionMode && !info.isGuide && info.index >= 0) {
        setSelectedIndexes([info.index]);
      }
    },

    onEdit: ({ updatedData, editType }) => {
      // Always update internal state for responsive UI
      setFeatures(updatedData);
      // Sync to Python on meaningful edits
      if (SYNC_EVENTS.has(editType)) {
        syncToModel(updatedData, editType);
      }
    },
  });
}

/** Delete features at the given indexes from a FeatureCollection. */
export function deleteFeatures(featureCollection, indexes) {
  const indexSet = new Set(indexes);
  return {
    type: "FeatureCollection",
    features: featureCollection.features.filter((_, i) => !indexSet.has(i)),
  };
}
