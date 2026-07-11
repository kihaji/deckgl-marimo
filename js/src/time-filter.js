/**
 * Time-filter helpers for the GPU sliding-window animation
 * (DataFilterExtension). Pure functions, unit-testable.
 *
 * Ported from deckgl_dash's utils/timeFilter.js.
 */
import { DataFilterExtension } from "@deck.gl/extensions";

/**
 * Compute the GPU filter bounds for a sliding window ending at head time T.
 * Returns the hard `range` ([T-window, T]) and an optional `soft` fade range.
 */
export function computeFilterRange(T, tf) {
  const w = tf.window || 0;
  const range = [T - w, T];
  const soft = (typeof tf.softEdge === "number" && tf.softEdge > 0)
    ? [T - w - tf.softEdge, T + tf.softEdge]
    : null;
  return { range, soft };
}

/**
 * Decide whether a layer should receive the time filter range.
 * Honors an explicit `layerIds` allowlist, otherwise auto-detects any layer
 * carrying a DataFilterExtension (so basemap/tile layers are never filtered).
 */
export function isFilterTarget(layer, tf) {
  if (!layer) return false;
  if (Array.isArray(tf.layerIds)) {
    return tf.layerIds.includes(layer.id);
  }
  const exts = layer.props && layer.props.extensions;
  return Array.isArray(exts) && exts.some((e) => e instanceof DataFilterExtension);
}

/**
 * Return a new layers array where each filter-target layer is cloned with the
 * window's `filterRange` (and `filterSoftRange`). `layer.clone` only overrides
 * a GPU uniform — no re-tessellation — so this is cheap to call every frame.
 */
export function applyRangeToLayers(layers, T, tf) {
  if (!tf || !Array.isArray(layers)) return layers;
  const { range, soft } = computeFilterRange(T, tf);
  return layers.map((layer) => {
    if (!isFilterTarget(layer, tf)) return layer;
    const overrides = soft ? { filterRange: range, filterSoftRange: soft } : { filterRange: range };
    return layer.clone(overrides);
  });
}

/** Resolve the head time used for the current render (paused -> current; playing -> live head). */
export function resolveHeadTime(tf, head) {
  if (tf && !tf.playing && typeof tf.current === "number") return tf.current;
  if (head != null) return head;
  if (tf && typeof tf.current === "number") return tf.current;
  if (tf && Array.isArray(tf.domain)) return tf.domain[0] + (tf.window || 0);
  return 0;
}

/** Advance the playback head by dt seconds, honoring speed and looping. */
export function advanceHead(head, dt, tf) {
  const domain = Array.isArray(tf.domain) ? tf.domain : [0, 0];
  const w = tf.window || 0;
  const speed = typeof tf.speed === "number" ? tf.speed : (domain[1] - domain[0]) / 20;
  const loop = tf.loop !== false;
  const start = domain[0] + w;
  const end = domain[1];
  let T = (head == null ? start : head) + speed * dt;
  if (T > end) {
    const span = end - start;
    T = (loop && span > 0) ? start + ((T - start) % span) : (loop ? start : end);
  }
  return T;
}
