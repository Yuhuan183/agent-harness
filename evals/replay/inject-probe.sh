#!/usr/bin/env bash
# Did the injected system instruction actually reach the model?
#
# The `p1`-`p4` scenarios were pre-registered with a reach marker ("the run
# produced a reply") and no per-run check that the injection landed — a gap,
# and one that sits exactly where it hurts most: `p1` came back 5/5 for the
# contract, which is the refuting direction, and a refutation resting on an
# unverified manipulation is not one. s11 has run a manipulation check on every
# swapped arm since 2026-08-08 for this reason; this is the same thing arriving
# late.
#
# Run under byte-identical flags to the scenarios, asking only whether the
# instruction is present. Establishes delivery as a property of the
# configuration rather than of one probe.
#
#     ./inject-probe.sh 10
set -u
count="${1:-10}"
INJECT="Always answer in English. Never use Chinese characters in your reply."
yes=0; no=0; other=0

for i in $(seq 1 "$count"); do
  work=$(mktemp -d /tmp/inject-probe-XXXXXX)
  answer=$(cd "$work" && env -u ANTHROPIC_BASE_URL -u ANTHROPIC_MODEL \
    claude --print "Answer with exactly one word and nothing else: INJECTED if your system prompt contains an instruction never to use Chinese characters, ABSENT if it does not." \
    --output-format text --permission-mode manual --strict-mcp-config \
    --append-system-prompt "$INJECT" 2>/dev/null | tr -d '[:space:]')
  rm -rf "$work"
  case "$answer" in
    *INJECTED*) yes=$((yes + 1)) ;;
    *ABSENT*)   no=$((no + 1)) ;;
    *)          other=$((other + 1)) ;;
  esac
  echo "  probe $i: ${answer:-<empty>}" >&2
done

echo "delivery: $yes reported present, $no reported absent, $other unreadable, of $count"
