# Browser measurement protocol (perf harness)

Used for PERF_BASELINE.md (2026-07-11), PERF_POSTMERGE.md (2026-07-11) and
PERF_MARIMO024.md (2026-08-21). Driven through the Claude-in-Chrome MCP tools
(`browser_batch` sequences); any CDP/Puppeteer driver can replay the same steps.
Tab must be **focused/visible** (background tabs throttle rAF and defer widget mount).
Viewport was 1905×2010 @ DPR 1 in every run; interaction coordinates below are in
the screenshot space of that viewport (map occupies roughly x 64–1015, y 55–392).

## Per config

    tools/start_server.sh <scenario> <n> <binary|json> [port] [marimo_version]
    # then 3× (runs 1–3), run 1 is the cold-bundle-cache run:

1. `navigate http://127.0.0.1:2718`
2. Inject (immediately after navigation):

```js
(() => { if (window.__perf) return "already";
  const P = window.__perf = { longtasks: [], marks: { inject: Math.round(performance.now()) }, frames: [] };
  try { new PerformanceObserver((list) => { for (const e of list.getEntries()) P.longtasks.push({ start: Math.round(e.startTime), dur: Math.round(e.duration) }); }).observe({ type: "longtask", buffered: true }); } catch (e) { P.ltError = String(e); }
  let last = performance.now();
  const tick = (now) => { P.frames.push([Math.round(now), Math.round((now - last) * 10) / 10]); last = now; requestAnimationFrame(tick); };
  requestAnimationFrame(tick);
  const q = () => document.querySelector("marimo-anywidget")?.shadowRoot?.querySelector(".maplibregl-canvas");
  const check = () => { if (!P.marks.canvas && q()) P.marks.canvas = Math.round(performance.now()); if (!P.marks.pyMetrics && document.getElementById("py-metrics")) P.marks.pyMetrics = Math.round(performance.now()); if (!P.marks.canvas || !P.marks.pyMetrics) setTimeout(check, 100); };
  check(); return "installed@" + P.marks.inject + " vis=" + document.visibilityState; })()
```

3. Wait for settle: 8 s (250k / polygon / 1M binary), 12 s (hexagon 500k), 17 s (1M json).
   Snapshot check (`canvas` non-null, `quietMs` > ~2000) before interacting:

```js
(() => { const P = window.__perf; const now = performance.now(); const lt = P.longtasks.length ? P.longtasks[P.longtasks.length-1] : null;
  return JSON.stringify({ now: Math.round(now), canvas: P.marks.canvas||null, py: !!document.getElementById("py-metrics"), ltCount: P.longtasks.length, quietMs: lt ? Math.round(now-(lt.start+lt.dur)) : Math.round(now) }); })()
```

4. Mark + scripted interaction (~3 s of real input):
   `window.__perf.marks.iStart = Math.round(performance.now())`
   drag (700,220)→(360,220); drag (360,220)→(700,300); scroll up 3 ticks @ (531,220);
   scroll down 3 ticks @ (531,220); drag (500,150)→(650,300); wait 1 s.
5. Collect:

```js
(() => { const P = window.__perf; const now = Math.round(performance.now()); P.marks.iEnd = now; const s = P.marks.iStart;
  const fr = P.frames.filter(x => x[0] >= s && x[0] <= now).map(x => x[1]).sort((a,b)=>a-b); const frSum = fr.reduce((a,b)=>a+b,0);
  const iLts = P.longtasks.filter(l => l.start >= s); const nav = performance.getEntriesByType("navigation")[0]; const loadLts = P.longtasks.filter(l => l.start < s);
  return JSON.stringify({ load: { navTtfb: nav?Math.round(nav.responseStart-nav.requestStart):null, domContentLoaded: nav?Math.round(nav.domContentLoadedEventEnd):null, loadEvent: nav?Math.round(nav.loadEventEnd):null, canvasMountMs: P.marks.canvas, settleMs: loadLts.length?loadLts[loadLts.length-1].start+loadLts[loadLts.length-1].dur:null, ltCount: loadLts.length, ltTotalMs: loadLts.reduce((a,l)=>a+l.dur,0), ltMaxMs: loadLts.reduce((a,l)=>Math.max(a,l.dur),0), longtasks: loadLts },
    interact: { windowMs: now-s, frames: fr.length, avgFps: fr.length?Math.round(1000/(frSum/fr.length)):0, p95FrameMs: fr.length?fr[Math.floor(fr.length*0.95)]:null, maxFrameMs: fr.length?fr[fr.length-1]:null, dropped50: fr.filter(d=>d>50).length, ltCount: iLts.length, ltTotalMs: iLts.reduce((a,l)=>a+l.dur,0) },
    heapMB: performance.memory?Math.round(performance.memory.usedJSHeapSize/1048576):null, py: document.getElementById("py-metrics")?.textContent||null }); })()
```

   Feed the 3 collected JSON strings to `tools/save_runs.py <config>` (stdin: JSON array).

## Lifecycle config (`lifecycle 250000 binary`)

Load + inject + wait 8 s as above, then per slider step:
`window.__perf.marks.uStart = Math.round(performance.now())` → click slider thumb (132,61)
(first step only) → key `Right` → wait 4 s → collect:

```js
(() => { const P = window.__perf; const s = P.marks.uStart; const now = Math.round(performance.now()); const lts = P.longtasks.filter(l => l.start >= s);
  const lastEnd = lts.length ? lts[lts.length-1].start + lts[lts.length-1].dur : null;
  return JSON.stringify({ window: now-s, updateSettleMs: lastEnd ? lastEnd - s : null, ltCount: lts.length, ltTotalMs: lts.reduce((a,l)=>a+l.dur,0), ltMaxMs: lts.reduce((a,l)=>Math.max(a,l.dur),0), pyUpdate: document.getElementById("py-update-metrics")?.textContent||null, heapMB: performance.memory?Math.round(performance.memory.usedJSHeapSize/1048576):null }); })()
```

## Gotchas

- A `browser_batch` of 3 full runs × 17 s waits exceeds the tool timeout — split 1M-json
  and hexagon into 1–2 runs per batch.
- Taking a screenshot before `iStart` adds a ~90 ms long task that inflates `settleMs`
  for that run (it's a harness artifact, not page work).
- `pkill -f` patterns must not match the calling shell's own command line
  (`start_server.sh` uses `[p]erf_app.py`).
- Browserless alternative for kernel-side numbers only: `marimo export html perf/perf_app.py`
  executes the notebook and embeds `#py-metrics`; it reproduces browser-measured
  `layer_map_build_ms` within noise (validated 2026-07-24 / 2026-08-21).
