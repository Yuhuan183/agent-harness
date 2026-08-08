#!/usr/bin/env bash
# The null needs a control. If the contract never reached the headless session
# at all, all three arms would be identical by construction and the result would
# read as "no effect" while actually measuring nothing. The manipulation check
# is what separates those two, and one observation per arm leaves a 25% chance
# of having guessed the pair. Repeat it.
set -uo pipefail
cd "$(dirname "$0")"
OUT=runs/preflight.tsv
[ -f "$OUT" ] || printf 'arm\trep\tanswer\texpected\tlanded\n' > "$OUT"
for arm in a b c; do
  for rep in 1 2 3; do
    line=$(./run.py --clause provider-routing --arm "$arm" --preflight 2>/dev/null \
      | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["answer"], d["expected"], d["landed"])')
    printf '%s\t%s\t%s\n' "$arm" "$rep" "$(echo "$line" | tr ' ' '\t')" >> "$OUT"
    echo "arm $arm rep $rep: $line"
  done
done
echo PREFLIGHT COMPLETE
