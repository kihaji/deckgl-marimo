/**
 * Viewport readback (JS -> Python `viewport` traitlet).
 *
 * Builds the payload the Python side exposes as `widget.value["viewport"]`
 * and `Map.bounds`. Kept free of MapLibre imports so it is unit-testable
 * with a stub map object.
 */

/**
 * Snapshot the camera: center/zoom/pitch/bearing plus the visible extent.
 *
 * `bounds` is `[[west, south], [east, north]]` (lower-left, upper-right) —
 * the same shape `Map.fit_bounds()` accepts, so it round-trips. MapLibre's
 * `getBounds()` returns the axis-aligned box around the (possibly pitched,
 * trapezoidal) visible area, with unwrapped longitudes across the
 * antimeridian; both are passed through unchanged.
 *
 * @param {object} map MapLibre map (or any object with the same getters)
 * @returns {{longitude:number, latitude:number, zoom:number, pitch:number, bearing:number, bounds?:number[][]}}
 */
export function viewportPayload(map) {
  const center = map.getCenter();
  const payload = {
    longitude: center.lng,
    latitude: center.lat,
    zoom: map.getZoom(),
    pitch: map.getPitch(),
    bearing: map.getBearing(),
  };
  const b = typeof map.getBounds === "function" ? map.getBounds() : null;
  if (b) {
    const sw = b.getSouthWest();
    const ne = b.getNorthEast();
    payload.bounds = [
      [sw.lng, sw.lat],
      [ne.lng, ne.lat],
    ];
  }
  return payload;
}
