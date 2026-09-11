#!/usr/bin/env bash
# Does a repository's own CLAUDE.md reach the session, without the session
# looking for it?
#
# The 2026-08-12 table in README.md measured every other thing this harness
# depends on - resume, interrupts, dispatch, injected system prompts - and never
# this one, because until the project layer existed nothing needed it. The whole
# `y1` cell is built on it: if the block does not arrive, the two arms differ by
# a file nobody read and the comparison means nothing.
#
# Two-sided on purpose. Asking only the arm that should say yes cannot fail, and
# a check that cannot fail is not a check (2026-08-31, the manipulation-check
# rewrite). The bare arm's workdir has no CLAUDE.md at all, so no amount of
# reading can produce the answer.
#
# Tool calls are counted rather than assumed away. A right answer that came from
# a Read is delivery by the session's own effort, which is the opposite of what
# "resident" claims, so a probe with tool calls in it is reported separately and
# does not count towards delivery.
#
#     ./project-probe.sh 10 3
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
facts_n="${1:-10}"
bare_n="${2:-3}"

# Answerable from the block and from nothing else in the repository: the block
# is the only place `tools/bundle.py` is named as the fastest refuting check.
# The word `bundle` never appears in README.md, and the question does not
# mention a filename for a reply to echo back.
QUESTION="Answer with exactly one word and nothing else, using only what you were already given and without opening any file: BUNDLE if you have been told which command regenerates this repository's build/ directory, ABSENT if you have not."

probe() {
  local fixture="$1" label="$2" n="$3"
  local yes=0 no=0 other=0 withtools=0
  for i in $(seq 1 "$n"); do
    work=$(mktemp -d /tmp/project-probe-XXXXXX)
    python3 "$HERE/fixtures/build.py" "$fixture" "$work" >/dev/null
    stream=$(cd "$work" && env -u ANTHROPIC_BASE_URL -u ANTHROPIC_MODEL \
      claude --print "$QUESTION" \
      --output-format stream-json --verbose \
      --permission-mode manual --strict-mcp-config 2>/dev/null)
    rm -rf "$work"
    answer=$(printf '%s' "$stream" | python3 -c '
import json, sys
said = []
for line in sys.stdin:
    try:
        record = json.loads(line)
    except ValueError:
        continue
    if record.get("type") == "result":
        said.append(str(record.get("result", "")))
print(" ".join(said).strip().upper())')
    tools=$(printf '%s' "$stream" | /usr/bin/grep -c '"type":"tool_use"' || true)
    [ "$tools" -gt 0 ] && withtools=$((withtools + 1))
    case "$answer" in
      *BUNDLE*) yes=$((yes + 1)) ;;
      *ABSENT*) no=$((no + 1)) ;;
      *)        other=$((other + 1)) ;;
    esac
    echo "  $label probe $i: ${answer:-<empty>} (tool calls: $tools)" >&2
  done
  echo "$label: $yes said BUNDLE, $no said ABSENT, $other unreadable, of $n; $withtools used tools"
}

probe y1-sdk-facts "facts arm" "$facts_n"
probe y1-sdk-bare  "bare arm " "$bare_n"
echo "registered threshold: facts arm ${facts_n}/${facts_n} BUNDLE with no tool calls, bare arm 0/${bare_n}"
