/**
 * Zoom-gated layer visibility.
 *
 * Python emits `minZoom`/`maxZoom` on layer specs; these are widget-side
 * gates folded into each spec's `visible` prop (deck.gl never sees them —
 * the layer factory peels them off).
 */

/** True when the current zoom is inside the spec's [minZoom, maxZoom] range. */
export function isInZoomRange(spec, zoom) {
  return (
    (spec.minZoom == null || zoom >= spec.minZoom) &&
    (spec.maxZoom == null || zoom <= spec.maxZoom)
  );
}

/**
 * Fold min/max zoom gating into each spec's `visible` prop.
 *
 * Preserves the user-supplied visible by stashing it once on `_userVisible`,
 * so repeated calls with a changing zoom are idempotent.
 */
export function applyZoomVisibility(specs, zoom) {
  for (const spec of specs) {
    if (spec.minZoom == null && spec.maxZoom == null) continue;
    if (spec._userVisible === undefined) {
      spec._userVisible = spec.visible !== false;
    }
    spec.visible = spec._userVisible && isInZoomRange(spec, zoom);
  }
}

/**
 * Compact fingerprint of every gated spec's in-range state at this zoom.
 *
 * Returns null when no spec is zoom-gated. The zoom event handler compares
 * consecutive keys so it only rebuilds layers when at least one gated
 * layer's effective visibility actually flips.
 */
export function zoomVisibilityKey(specs, zoom) {
  let hasGated = false;
  let key = "";
  for (const s of specs) {
    if (s.minZoom == null && s.maxZoom == null) continue;
    hasGated = true;
    key += `${s.id}:${isInZoomRange(s, zoom) ? 1 : 0}|`;
  }
  return hasGated ? key : null;
}
