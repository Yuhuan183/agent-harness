#!/usr/bin/env bash
# One pre-registered batch: five runs of a scenario, each graded as it lands.
#
# Sequential on purpose. `r1` interrupts turn 1 at a wall clock, so anything
# that slows the machine moves where the cut falls — running these in parallel
# would make the interrupt point a function of the batch's own load. The cost
# is wall time, which a batch has to spend anyway.
#
# Grading happens per run rather than at the end so a broken scenario shows up
# on run 1 instead of after all five are paid for. Verdicts are appended to
# results.tsv; the exit status of grade.py is the record (0 correct, 1
# incorrect, 2 invalid), and an invalid run is data about the scenario, never
# something to drop.
#
#     ./batch.sh r1-interrupted-resume 5
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scenario="${1:?usage: batch.sh <scenario-stem> [count]}"
count="${2:-5}"
spec="$HERE/scenarios/$scenario.md"
[ -f "$spec" ] || { echo "no such scenario: $spec" >&2; exit 1; }

results="$HERE/runs/results.tsv"
[ -s "$results" ] || printf 'scenario\trun\tverdict\texit\tdetail\n' > "$results"

for seed in $(seq 1 "$count"); do
  out="$HERE/runs/$scenario-$(printf '%03d' "$seed")"
  # Resumable without paying twice, and without silently shrinking n.
  #
  # The guard was "directory exists", and on 2026-08-12 that quietly took a
  # batch from five runs to four: a killed run had left a directory holding
  # nothing but an empty `telemetry/`, and the restart skipped the seed. A
  # sample size that changes without anyone declaring it is the thing
  # pre-registration exists to prevent, so completeness is judged by the
  # artifact a finished run leaves, not by the directory it made on its way in.
  if [ -f "$out/meta.json" ]; then
    echo "=== $scenario seed $seed already complete at $out, skipping" >&2
    continue
  fi
  if [ -d "$out" ]; then
    echo "=== $scenario seed $seed: removing incomplete run at $out" >&2
    rm -rf "$out"
  fi
  echo "=== $scenario seed $seed -> $out" >&2
  "$HERE/run.py" --scenario "$spec" --out "$out" >&2
  verdict=$("$HERE/grade.py" --run "$out" > "$out/verdict.json" 2>&1; echo $?)
  detail=$(python3 -c "
import json, sys
try:
    report = json.load(open(sys.argv[1]))
except Exception as error:
    print(f'unreadable verdict: {error}'); raise SystemExit
outcome = report['outcome']
bits = [f\"marker={outcome['marker_present']}\"]
for key in ('turns_without_decision_line', 'duplicated', 'missing',
            'leaf_dispatches', 'tokens_at_interrupt'):
    if key in outcome:
        bits.append(f'{key}={outcome[key]}')
bits.append(f\"crit3_open={report['criterion_3']['unreconciled']}\")
print(' '.join(str(bit) for bit in bits))
" "$out/verdict.json")
  name=$(python3 -c "
import json, sys
print(json.load(open(sys.argv[1]))['verdict'])" "$out/verdict.json" 2>/dev/null || echo "?")
  printf '%s\t%s\t%s\t%s\t%s\n' \
    "$scenario" "$(basename "$out")" "$name" "$verdict" "$detail" >> "$results"
  echo "    $name (exit $verdict) $detail" >&2
done

echo "--- $scenario done; results in $results" >&2
