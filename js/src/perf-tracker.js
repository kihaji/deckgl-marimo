/**
 * FPS / performance metrics tracker.
 * Uses requestAnimationFrame to measure frame times and periodically
 * pushes metrics back to the Python model.
 */
export function createPerfTracker(model) {
  const frameTimes = [];
  const maxSamples = 60;
  let lastTime = performance.now();
  let lastPush = 0;
  let animId = null;
  let deckRef = null; // set externally to access deck.metrics

  function tick(now) {
    const dt = now - lastTime;
    lastTime = now;
    frameTimes.push(dt);
    if (frameTimes.length > maxSamples) frameTimes.shift();

    // Push metrics to Python every 500ms
    if (now - lastPush > 500 && frameTimes.length > 5) {
      lastPush = now;
      const avg = frameTimes.reduce((a, b) => a + b, 0) / frameTimes.length;
      const fps = 1000 / avg;
      const min = Math.min(...frameTimes);
      const max = Math.max(...frameTimes);

      const metrics = {
        fps: Math.round(fps * 10) / 10,
        frameTimeAvg: Math.round(avg * 100) / 100,
        frameTimeMin: Math.round(min * 100) / 100,
        frameTimeMax: Math.round(max * 100) / 100,
      };

      // Try to get deck.gl internal metrics
      try {
        const dm = deckRef?.metrics;
        if (dm) {
          metrics.gpuTime = dm.gpuTime;
          metrics.cpuTime = dm.cpuTime;
          metrics.gpuTimePerFrame = dm.gpuTimePerFrame;
          metrics.cpuTimePerFrame = dm.cpuTimePerFrame;
          metrics.bufferMemory = dm.bufferMemory;
          metrics.textureMemory = dm.textureMemory;
        }
      } catch (e) {
        // deck metrics not available
      }

      model.set("perf_metrics", metrics);
      model.save_changes();
    }

    animId = requestAnimationFrame(tick);
  }

  return {
    start() {
      if (animId !== null) return; // idempotent — never double the rAF loop
      lastTime = performance.now();
      frameTimes.length = 0;
      animId = requestAnimationFrame(tick);
    },
    stop() {
      if (animId !== null) {
        cancelAnimationFrame(animId);
        animId = null;
      }
    },
    setDeck(d) { deckRef = d; },
  };
}
