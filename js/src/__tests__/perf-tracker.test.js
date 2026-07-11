import { describe, expect, it, vi } from "vitest";
import { createPerfTracker } from "../perf-tracker.js";

function stubRaf() {
  let nextId = 1;
  const scheduled = new Map();
  vi.stubGlobal("requestAnimationFrame", (cb) => {
    const id = nextId++;
    scheduled.set(id, cb);
    return id;
  });
  vi.stubGlobal("cancelAnimationFrame", (id) => scheduled.delete(id));
  return scheduled;
}

describe("createPerfTracker", () => {
  it("start is idempotent — never doubles the rAF loop", () => {
    const scheduled = stubRaf();
    const model = { set: vi.fn(), save_changes: vi.fn() };
    const perf = createPerfTracker(model);
    perf.start();
    perf.start();
    expect(scheduled.size).toBe(1);
    perf.stop();
    vi.unstubAllGlobals();
  });

  it("stop cancels the pending frame and allows a clean restart", () => {
    const scheduled = stubRaf();
    const model = { set: vi.fn(), save_changes: vi.fn() };
    const perf = createPerfTracker(model);
    perf.start();
    perf.stop();
    expect(scheduled.size).toBe(0);
    perf.start();
    expect(scheduled.size).toBe(1);
    perf.stop();
    vi.unstubAllGlobals();
  });

  it("pushes no metrics while stopped", () => {
    const scheduled = stubRaf();
    const model = { set: vi.fn(), save_changes: vi.fn() };
    const perf = createPerfTracker(model);
    perf.start();
    perf.stop();
    expect(model.set).not.toHaveBeenCalled();
    expect(scheduled.size).toBe(0);
    vi.unstubAllGlobals();
  });
});
