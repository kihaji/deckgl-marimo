"""Persist browser-harness runs collected per perf/tools/browser_protocol.md.

Usage:
    python perf/tools/save_runs.py <config_name> < runs.json

stdin is a JSON array of the per-run "collect" payloads (strings or dicts) in
run order. Each becomes ``<PERF_RESULTS_DIR>/<config>_run<i>.json`` and a
one-line summary is printed. ``PERF_RESULTS_DIR`` defaults to
``perf/results/latest``.
"""

from __future__ import annotations

import contextlib
import json
import os
import sys
from typing import Any


def _normalize(raw: Any) -> dict[str, Any]:
    d = json.loads(raw) if isinstance(raw, str) else raw
    py = d.get("py")
    if isinstance(py, str):
        with contextlib.suppress(ValueError):
            py = json.loads(py)
    return {"load": d["load"], "interact": d["interact"], "heapMB": d.get("heapMB"), "py": py}


def main() -> None:
    config = sys.argv[1]
    runs = json.load(sys.stdin)
    out_dir = os.environ.get("PERF_RESULTS_DIR", "perf/results/latest")
    os.makedirs(out_dir, exist_ok=True)
    for i, raw in enumerate(runs, 1):
        rec = {"config": config, "run": i, **_normalize(raw)}
        with open(f"{out_dir}/{config}_run{i}.json", "w") as f:
            json.dump(rec, f, indent=1)
        load, inter, py = rec["load"], rec["interact"], rec["py"]
        build = py.get("layer_map_build_ms") if isinstance(py, dict) else "?"
        print(
            f"{config} run{i}: build={build}ms canvas={load['canvasMountMs']} settle={load['settleMs']} "
            f"lt={load['ltCount']}/{load['ltTotalMs']}/{load['ltMaxMs']} fps={inter['avgFps']} "
            f"p95={inter['p95FrameMs']} max={inter['maxFrameMs']} drop={inter['dropped50']} "
            f"ilt={inter['ltCount']} heap={rec['heapMB']}"
        )


if __name__ == "__main__":
    main()
