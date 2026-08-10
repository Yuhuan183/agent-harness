#!/usr/bin/env bash
# Run one clause × one arm × the listed scenarios × N seeds, sequentially.
#
# Replaces pilot.sh, which had two defects the first batch exposed. It piped
# run.py's stderr to /dev/null, so nothing recorded which contract each run
# actually executed under - every arm-B row was a claim about a condition no
# artifact could confirm. And it built its TSV with `tr ' ' '\t'`, which split
# the two-word verdict into two fields and left the data in a different column
# order than the header. Both are fixed here: provenance comes from run.py's
# per-run .meta.json, and fields are emitted one at a time.
#
# Sequential on purpose. Arms B and C swap the deployed contract, so two runs at
# once would race on one file.
#
#   ./batch.sh provider-routing c "p1-cross-provider p2-single-provider" 5
set -uo pipefail
cd "$(dirname "$0")"

CLAUSE=${1:?clause}
ARM=${2:?arm}
SCENARIOS=${3:?space-separated scenario stems}
SEEDS=${4:-5}
SOURCE=../../../main/claude/CLAUDE.contract.md
RESULTS=runs/results.tsv
mkdir -p runs
[ -f "$RESULTS" ] || printf 'clause\tarm\tscenario\tseed\tverdict\tskills\tcontract_sha\tnames_left\n' > "$RESULTS"

for scenario in $SCENARIOS; do
  for seed in $(seq 1 "$SEEDS"); do
    out="runs/${CLAUSE}-${ARM}-${scenario}-${seed}.jsonl"
    if [ -f "$out" ]; then echo "skip $out"; continue; fi

    ./run.py --clause "$CLAUSE" --arm "$ARM" \
             --scenario "scenarios/${scenario}.md" --out "$out" >/dev/null 2>&1

    if ! diff -q <(cat "$HOME/.claude/CLAUDE.md") "$SOURCE" >/dev/null; then
      echo "ABORT: contract not restored after ${scenario}-${ARM}-${seed}" >&2
      exit 1
    fi

    meta="${out%.jsonl}.meta.json"
    if [ ! -f "$out" ] || [ ! -f "$meta" ]; then
      printf '%s\t%s\t%s\t%s\trun-failed\t-\t-\t-\n' \
        "$CLAUSE" "$ARM" "$scenario" "$seed" >> "$RESULTS"
      echo "FAILED ${scenario}-${ARM}-${seed}"
      continue
    fi

    read -r verdict skills < <(./grade.py --events "$out" \
        --scenario "scenarios/${scenario}.md" 2>/dev/null \
      | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["verdict"], ",".join(d["skills_invoked"]) or "-")')
    read -r sha names < <(python3 -c "
import json; m=json.load(open('$meta'))
print(m['contract_sha256_in_effect'][:12], m['clause_name_mentions_in_effect'])")

    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
      "$CLAUSE" "$ARM" "$scenario" "$seed" "$verdict" "$skills" "$sha" "$names" >> "$RESULTS"
    echo "done ${scenario}-${ARM}-${seed}: ${verdict} (${skills}) contract=${sha} names=${names}"
  done
done
echo "BATCH COMPLETE: $CLAUSE arm $ARM"
