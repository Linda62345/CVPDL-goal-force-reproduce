#!/bin/bash
# Overnight job queue (2026-11-25). Runs jobs from logs/overnight/queue.txt in file order, one at a time.
# Line format:  ID<TAB>shell command      (lines starting with # are ignored)
# done marker: logs/overnight/done/ID.ok ; failures: ID.fail (after 1 retry). Jobs must themselves skip existing outputs.
# New lines can be appended / inserted while running; the runner re-reads the file after every job.
# Stop: touch logs/overnight/STOP
cd "$(dirname "$0")/../.."
Q=logs/overnight/queue.txt; D=logs/overnight/done
WAIT_PID=${1:-}
if [ -n "$WAIT_PID" ]; then
  echo "[runner] waiting for PID $WAIT_PID $(date '+%F %T')"
  while kill -0 "$WAIT_PID" 2>/dev/null; do sleep 30; done
fi
echo "[runner] start $(date '+%F %T')"
while [ ! -f logs/overnight/STOP ]; do
  ran=0
  while IFS=$'\t' read -r id cmd; do
    [[ -z "$id" || "$id" == \#* ]] && continue
    [[ -f "$D/$id.ok" || -f "$D/$id.fail" ]] && continue
    for attempt in 1 2; do
      echo "[runner] $(date '+%F %T') START $id (attempt $attempt)"
      t0=$(date +%s)
      bash -c "$cmd" > "logs/overnight/$id.log" 2>&1
      rc=$?
      dt=$(( $(date +%s) - t0 ))
      echo "{\"id\":\"$id\",\"attempt\":$attempt,\"rc\":$rc,\"sec\":$dt,\"end\":\"$(date '+%F %T')\"}" >> logs/overnight/timings.jsonl
      if [ $rc -eq 0 ]; then touch "$D/$id.ok"; echo "[runner] $(date '+%F %T') OK $id (${dt}s)"; break; fi
      echo "[runner] $(date '+%F %T') FAIL $id rc=$rc (${dt}s)"
      cp "logs/overnight/$id.log" "logs/overnight/$id.attempt$attempt.log"
      [ $attempt -eq 2 ] && touch "$D/$id.fail"
    done
    ran=1
    break   # re-read queue after every job (allows insertion at the top)
  done < "$Q"
  [ $ran -eq 0 ] && sleep 60
done
echo "[runner] stopped $(date '+%F %T')"
