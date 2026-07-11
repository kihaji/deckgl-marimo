/**
 * Time-filter rAF animation engine: advances the sliding-window head time
 * while playing and pushes the GPU filterRange to the overlay without
 * rebuilding layers. The widget reports the throttled head back to Python
 * as `current_time`.
 */
import { advanceHead, applyRangeToLayers, resolveHeadTime } from "./time-filter.js";

// Throttle interval for reporting the playback head back to Python (~8 Hz).
const REPORT_INTERVAL_MS = 120;

/**
 * @param {Object} opts
 * @param {Object} opts.model - anywidget model (reads `time_filter`, writes `current_time`)
 * @param {Object} opts.overlay - deck.gl MapboxOverlay
 * @param {() => Array} opts.getBaseLayers - returns the current base layer array
 */
export function createTimeFilterAnimation({ model, overlay, getBaseLayers }) {
  let rafId = null;
  let head = null;
  let lastFrameTs = null;
  let lastReported = 0;

  const tf = () => model.get("time_filter") || null;
  const active = () => {
    const cfg = tf();
    return cfg && Object.keys(cfg).length > 0;
  };

  function applyFilterRange(T) {
    const cfg = tf();
    if (!cfg) return;
    overlay.setProps({ layers: applyRangeToLayers(getBaseLayers(), T, cfg) });
  }

  function tick(ts) {
    const cfg = tf();
    if (!cfg || !cfg.playing) {
      rafId = null;
      return;
    }
    if (lastFrameTs == null) lastFrameTs = ts;
    const dt = (ts - lastFrameTs) / 1000;
    lastFrameTs = ts;

    head = advanceHead(head, dt, cfg);
    applyFilterRange(head);
    if (ts - lastReported >= REPORT_INTERVAL_MS) {
      lastReported = ts;
      model.set("current_time", head);
      model.save_changes();
    }
    rafId = requestAnimationFrame(tick);
  }

  /** Reconcile with the current time_filter: start/stop playback, scrub when paused. */
  function sync() {
    if (!active()) {
      if (rafId != null) {
        cancelAnimationFrame(rafId);
        rafId = null;
      }
      return;
    }
    const cfg = tf();
    if (head == null) head = resolveHeadTime(cfg, null);

    if (cfg.playing) {
      if (rafId == null) {
        lastFrameTs = null; // reset dt so resume doesn't jump
        rafId = requestAnimationFrame(tick);
      }
    } else {
      if (rafId != null) {
        cancelAnimationFrame(rafId);
        rafId = null;
      }
      // Paused scrubbing: the incoming `current` is authoritative.
      if (typeof cfg.current === "number") head = cfg.current;
      applyFilterRange(head);
    }
  }

  return {
    sync,
    /** Re-apply the current window after base layers are rebuilt. */
    reapply() {
      if (active() && head != null) applyFilterRange(head);
    },
    stop() {
      if (rafId != null) {
        cancelAnimationFrame(rafId);
        rafId = null;
      }
    },
  };
}
