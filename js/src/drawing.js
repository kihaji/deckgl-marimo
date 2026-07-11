/**
 * Drawing controller: owns the feature collection and selection state,
 * builds the editable layer, syncs edits back to Python, and adjusts map
 * interactions (cursor, drag-pan, double-click zoom) per mode.
 *
 * The anywidget counterpart of deckgl_dash's useDrawing hook.
 */
import {
  ACTIVE_DRAWING_MODES,
  DRAG_DRAW_MODES,
  createEditableLayer,
  deleteFeatures,
  getCursorForMode,
} from "./drawing-manager.js";

const EMPTY_FEATURE_COLLECTION = { type: "FeatureCollection", features: [] };

export function createDrawingController({ model, map, onLayersChanged }) {
  let features = model.get("drawing_features") || EMPTY_FEATURE_COLLECTION;
  let selectedIndexes = [];
  let prevMode = null;
  let selfUpdate = false; // guard: our own model writes echo back as change events

  const cfg = () => model.get("drawing_config") || {};
  const isActive = () => {
    const mode = cfg().mode;
    return Boolean(mode && mode !== "view");
  };

  function syncToModel(updated, editType) {
    selfUpdate = true;
    try {
      model.set("drawing_features", updated);
      model.set("drawing_event", {
        type: editType,
        featureCount: updated.features.length,
        timestamp: Date.now(),
      });
      model.save_changes();
    } finally {
      selfUpdate = false;
    }
  }

  function setFeatures(updated) {
    features = updated;
    onLayersChanged();
  }

  function setSelectedIndexes(indexes) {
    selectedIndexes = indexes;
    onLayersChanged();
  }

  /** Adjust map interactions + cursor for the current mode. */
  function applyInteractions() {
    const mode = cfg().mode || "view";
    const active = isActive();
    if (DRAG_DRAW_MODES.has(mode)) {
      map.dragPan.disable();
    } else {
      map.dragPan.enable();
    }
    if (active) {
      map.doubleClickZoom.disable();
    } else {
      map.doubleClickZoom.enable();
    }
    map.getCanvas().style.cursor = active ? getCursorForMode(mode) : "";
  }

  function handleConfigChange() {
    const config = cfg();
    // Clear selection when switching modes
    if (config.mode !== prevMode) {
      prevMode = config.mode;
      selectedIndexes = [];
    }
    // deleteSelected: act once, then reset the flag Python-side
    if (config.deleteSelected && selectedIndexes.length > 0) {
      const updated = deleteFeatures(features, selectedIndexes);
      features = updated;
      selectedIndexes = [];
      syncToModel(updated, "deleteFeature");
      selfUpdate = true;
      try {
        model.set("drawing_config", { ...config, deleteSelected: false });
        model.save_changes();
      } finally {
        selfUpdate = false;
      }
    }
    applyInteractions();
    onLayersChanged();
  }

  model.on("change:drawing_config", () => {
    if (!selfUpdate) handleConfigChange();
  });
  // External feature set (e.g. Python clears or seeds features)
  model.on("change:drawing_features", () => {
    if (selfUpdate) return;
    features = model.get("drawing_features") || EMPTY_FEATURE_COLLECTION;
    selectedIndexes = [];
    onLayersChanged();
  });

  // Initialize interactions for a config supplied at construction time
  if (isActive()) {
    prevMode = cfg().mode;
    applyInteractions();
  }

  return {
    /** The editable layer to append on top of the deck layers (or null). */
    getLayer() {
      if (!isActive()) return null;
      const config = cfg();
      return createEditableLayer(
        config,
        features,
        config.selectedFeatureIndexes?.length ? config.selectedFeatureIndexes : selectedIndexes,
        { setFeatures, setSelectedIndexes, syncToModel },
      );
    },
  };
}
