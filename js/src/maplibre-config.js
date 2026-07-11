/**
 * Composed basemap configuration: a base style plus extra MapLibre
 * sources and style layers, delivered from Python as the
 * `maplibre_config` traitlet ({style, sources, mapLayers, mapOptions}).
 *
 * Deliberately free of maplibre-gl imports so it stays unit-testable.
 */

/**
 * Pick the style to load: a non-empty config's style wins over the plain
 * basemap_style string; otherwise fall back.
 */
export function resolveStyle(config, basemapStyle, fallback) {
  if (config && config.style) return config.style;
  return basemapStyle || fallback;
}

/**
 * Apply a config's extra sources and layers onto the map. Idempotent —
 * safe to call after every style load (setStyle wipes user sources, so
 * this must re-run on the `style.load` event).
 */
export function applyConfigExtras(map, config) {
  if (!config) return;
  for (const [id, source] of Object.entries(config.sources || {})) {
    if (!map.getSource(id)) {
      map.addSource(id, source);
    }
  }
  for (const layer of config.mapLayers || []) {
    if (!map.getLayer(layer.id)) {
      map.addLayer(layer);
    }
  }
}
