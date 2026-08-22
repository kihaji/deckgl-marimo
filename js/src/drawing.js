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
  SELECTION_MODES,
  createEditableLayer,
  deleteFeatures,
  getCursorForMode,
} from "./drawing-manager.js";

const EMPTY_FEATURE_COLLECTION = { type: "FeatureCollection", features: [] };

/**
 * Does this pick start a drag the edit mode will handle itself? Edit handles
 * (vertices) always do; in translate mode so does a selected feature.
 */
export function pickStartsEditDrag(pick, mode, selectedIndexes) {
  if (!pick) return false;
  const guideType = pick.object && pick.object.properties && pick.object.properties.guideType;
  if (pick.isGuide && guideType === "editHandle") return true;
  return mode === "translate" && selectedIndexes.includes(pick.index);
}

/**
 * @param {object} opts
 * @param {object} opts.model anywidget model
 * @param {object} opts.map MapLibre map
 * @param {Function} opts.onLayersChanged re-render callback
 * @param {Function} [opts.pickDrawing] (x, y) => deck pick infos for the editable layer
 */
export function createDrawingController({ model, map, onLayersChanged, pickDrawing }) {
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

  // --- Drag guard ---------------------------------------------------------
  // The edit modes drag vertices/features through deck's event manager, but
  // MapLibre's own drag-pan handler would move the map at the same time
  // (nebula's cancelPan cannot stop native map handlers). When the pointer
  // goes down on something the edit mode will drag, suspend dragPan for the
  // rest of that gesture. onCancelPan (called by the edit mode) is the
  // second line of defence.
  let panSuspended = false;
  const suspendPan = () => {
    if (panSuspended) return;
    panSuspended = true;
    map.dragPan.disable();
  };
  const resumePan = () => {
    if (!panSuspended) return;
    panSuspended = false;
    applyInteractions(); // restores the per-mode dragPan state
  };
  const onPointerDown = (clientX, clientY) => {
    if (!isActive() || !pickDrawing) return;
    const mode = cfg().mode;
    if (!SELECTION_MODES.has(mode)) return;
    const rect = map.getCanvas().getBoundingClientRect();
    let picks = [];
    try {
      picks = pickDrawing(clientX - rect.left, clientY - rect.top) || [];
    } catch (e) {
      picks = [];
    }
    const config = cfg();
    const selected = config.selectedFeatureIndexes?.length ? config.selectedFeatureIndexes : selectedIndexes;
    if (picks.some((p) => pickStartsEditDrag(p, mode, selected))) suspendPan();
  };
  const onMouseDown = (ev) => onPointerDown(ev.clientX, ev.clientY);
  const onTouchStart = (ev) => {
    const t = ev.touches && ev.touches[0];
    if (t) onPointerDown(t.clientX, t.clientY);
  };
  const canvasContainer = map.getCanvasContainer();
  canvasContainer.addEventListener("mousedown", onMouseDown, true);
  canvasContainer.addEventListener("touchstart", onTouchStart, { capture: true, passive: true });
  window.addEventListener("mouseup", resumePan, true);
  window.addEventListener("touchend", resumePan, true);
  window.addEventListener("touchcancel", resumePan, true);

  return {
    /** Whether a drawing/editing mode (anything but "view") is active. */
    isActive,
    /** Remove window/canvas listeners. */
    destroy() {
      canvasContainer.removeEventListener("mousedown", onMouseDown, true);
      canvasContainer.removeEventListener("touchstart", onTouchStart, true);
      window.removeEventListener("mouseup", resumePan, true);
      window.removeEventListener("touchend", resumePan, true);
      window.removeEventListener("touchcancel", resumePan, true);
    },
    /**
     * The editable layer to append on top of the deck layers (or null).
     * In "view" mode the layer is still rendered (read-only ViewMode) when it
     * holds features, so loaded/drawn features do not vanish between edits.
     */
    getLayer() {
      const config = cfg();
      if (!isActive() && !(features.features && features.features.length)) return null;
      return createEditableLayer(
        { ...config, mode: config.mode || "view" },
        features,
        config.selectedFeatureIndexes?.length ? config.selectedFeatureIndexes : selectedIndexes,
        { setFeatures, setSelectedIndexes, syncToModel, onCancelPan: suspendPan },
      );
    },
  };
}
