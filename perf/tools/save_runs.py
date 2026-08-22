import json, sys
config = sys.argv[1]
runs = json.load(sys.stdin)  # list of collected JSON strings (or dicts)
import os; out_dir = os.environ.get("PERF_RESULTS_DIR", "perf/results/latest"); os.makedirs(out_dir, exist_ok=True)
for i, r in enumerate(runs, 1):
    d = json.loads(r) if isinstance(r, str) else r
    py = d.get("py")
    if isinstance(py, str):
        try: py = json.loads(py)
        except Exception: pass
    rec = {"config": config, "run": i, "load": d["load"], "interact": d["interact"], "heapMB": d.get("heapMB"), "py": py}
    with open(f"{out_dir}/{config}_run{i}.json", "w") as f:
        json.dump(rec, f, indent=1)
    L, I = d["load"], d["interact"]
    print(f"{config} run{i}: build={py.get('layer_map_build_ms') if isinstance(py,dict) else '?'}ms canvas={L['canvasMountMs']} settle={L['settleMs']} lt={L['ltCount']}/{L['ltTotalMs']}/{L['ltMaxMs']} fps={I['avgFps']} p95={I['p95FrameMs']} max={I['maxFrameMs']} drop={I['dropped50']} ilt={I['ltCount']} heap={d.get('heapMB')}")
