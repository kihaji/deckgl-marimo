#!/usr/bin/env bash
# usage: start_server.sh SCENARIO N MODE [PORT] [MARIMO_VERSION]
set -u
SCEN=$1; N=$2; MODE=$3; PORT=${4:-2718}; MV=${5:-0.24.0}
cd /home/kihaji/projects/deckgl-marimo
pkill -f "[p]erf_app.py" 2>/dev/null; sleep 1
LOG=/tmp/server_${SCEN}_${N}_${MODE}.log
PERF_SCENARIO=$SCEN PERF_N=$N PERF_MODE=$MODE setsid nohup uv run --with marimo==$MV marimo run perf/perf_app.py --headless --port $PORT --no-token > "$LOG" 2>&1 < /dev/null &
for i in $(seq 1 60); do
  if curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT" 2>/dev/null | grep -q 200; then echo "ready after ${i}s: $SCEN $N $MODE (marimo $MV) on :$PORT"; exit 0; fi
  sleep 1
done
echo "server failed to start; log tail:"; tail -20 "$LOG"; exit 1
