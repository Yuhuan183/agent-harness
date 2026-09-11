#!/usr/bin/env bash
# Does a skill that lives in the workdir reach the session, without HOME moving?
#
# T1 asks whether our skill machinery buys anything over a plain file carrying
# the same words. Answering it by removing a deployed skill would mean swapping
# a directory under the operator's own HOME; `arm.py` exists because swapping
# one live file already needed four guards, and a tree needs more. A skill that
# ships inside the fixture avoids the whole question - both arms then hold the
# same text in the same workdir and differ only in whether it is registered.
#
# That rests on an assumption nothing here has measured: that
# `<workdir>/.claude/skills/<name>/SKILL.md` puts its description in front of a
# `--print` session started with cwd set to that workdir. `test_contracts.py`
# establishes the shape for an interactive session in this checkout, which is
# not the same construct.
#
# Two-sided, and tool calls counted, for the reasons `project-probe.sh` states:
# a question only the skilled arm can pass cannot fail, and an answer that came
# from a Read is the session finding the file rather than being handed it.
#
#     ./skill-carrier-probe.sh 10 3
set -u
facts_n="${1:-10}"
bare_n="${2:-3}"

QUESTION="Answer with exactly one word and nothing else, using only the tools and skills you were already given and without opening any file: TIDEPOOL if a skill for recording tidepool observations is available to you, ABSENT if none is."

plant() {
  local work="$1"
  mkdir -p "$work/.claude/skills/tidepool-notes"
  cat > "$work/.claude/skills/tidepool-notes/SKILL.md" <<'SKILL'
---
name: tidepool-notes
description: |
  Record and normalise tidepool survey observations into the log format this
  project keeps. Use when writing up a shore survey, adding a species count, or
  reconciling two observers' notes for the same pool. Do not use for aquarium
  care, for open-water dive logs, or for anything that is not a tidepool survey.
---

# Tidepool notes

One observation per line. Species first, then count, then the pool identifier.
SKILL
  printf 'scratch\n' > "$work/notes.md"
}

probe() {
  local label="$1" n="$2" with_skill="$3"
  local yes=0 no=0 other=0 withtools=0
  for i in $(seq 1 "$n"); do
    work=$(mktemp -d /tmp/skill-carrier-XXXXXX)
    printf 'scratch\n' > "$work/notes.md"
    [ "$with_skill" = "yes" ] && plant "$work"
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
      *TIDEPOOL*) yes=$((yes + 1)) ;;
      *ABSENT*)   no=$((no + 1)) ;;
      *)          other=$((other + 1)) ;;
    esac
    echo "  $label probe $i: ${answer:-<empty>} (tool calls: $tools)" >&2
  done
  echo "$label: $yes said TIDEPOOL, $no said ABSENT, $other unreadable, of $n; $withtools used tools"
}

probe "workdir skill" "$facts_n" yes
probe "bare workdir " "$bare_n" no
echo "registered threshold: workdir arm ${facts_n}/${facts_n} TIDEPOOL with no tool calls, bare arm 0/${bare_n}"
