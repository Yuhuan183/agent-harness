#!/usr/bin/env python3
"""Append one line per fail-closed denial to ~/.claude/telemetry/denials.jsonl.

Why this exists. On 2026-08-08 the question "how often do our gates block, and
whom" had to be answered by grepping session transcripts, and the first three
attempts were wrong: 146 of the initial matches were file reads of the hooks'
own source, because the block strings live in their docstrings. `delegation.jsonl`
records dispatch start and stop with no denial counterpart, so the one thing the
gates do that a user actually feels was the one thing nothing recorded.

Scope is deliberately small. This is not a gate, not a counter with a threshold,
and not an escalation trigger. The direction that asked for a "three consecutive
denials" backstop was checked first and the threshold turned out to measure
ordinary work - commit-test-gate denies repeatedly while a red suite gets fixed,
which is the mechanism succeeding. Deciding whether any threshold is warranted
needs this data first, which is the whole reason it is collected before anything
consumes it.

Fail-open, unconditionally. A gate's decision must never depend on whether its
logging worked: `record` swallows every exception, and a caller that cannot even
import this module keeps its own fallback. The cost of a lost line is one
missing row; the cost of a raised exception inside a fail-closed hook is a
blocked commit nobody can explain.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

LOG = "~/.claude/telemetry/denials.jsonl"
# Where a row actually goes. The test suite runs these gates for real - scratch
# repositories, real `git commit`, real hook subprocesses - and a gate that
# derives its log path from HOME writes those fixture denials into the
# developer's own log. That is not hypothetical: on 2026-08-20 the machine-local
# log held 35,856 rows and 3 of them were real, so the one question this file
# exists to answer ("how often do our gates block, and whom") could not be
# answered from it. The suite sets this variable once, in `tests/support.py`.
#
# An override rather than test-detection inside the gate: a fail-closed hook
# must not take a different branch because it believes it is under test. This
# only moves where the row lands, so it cannot weaken any boundary - and a
# person who wants to silence the log can already delete the file.
ENV = "AGENT_DENIAL_LOG"


def log_path() -> str:
    """The log this process writes to: the override when set, else HOME's."""
    return os.path.expanduser(os.environ.get(ENV) or LOG)


def record(gate: str, reason: str, event: object = None, **detail: object) -> None:
    """Append one denial. Never raises, never blocks, never writes to stderr.

    `gate` is the hook's own name, `reason` a short stable code so rows can be
    counted without parsing prose, and `event` the hook payload when the caller
    has one - only its identifiers are kept, never its content.
    """
    try:
        row = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "gate": gate,
            "reason": reason,
        }
        if isinstance(event, dict):
            for key in ("session_id", "agent_type", "tool_name"):
                if event.get(key):
                    row[key] = event[key]
        row.update({k: v for k, v in detail.items() if v is not None})
        out = log_path()
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def main() -> int:
    """`denial_log.py --tail [n]` prints the most recent rows, for a human."""
    limit = 20
    if len(sys.argv) > 2 and sys.argv[2].isdigit():
        limit = int(sys.argv[2])
    try:
        with open(log_path(), encoding="utf-8") as handle:
            rows = handle.read().splitlines()
    except FileNotFoundError:
        print("no denials recorded yet")
        return 0
    for line in rows[-limit:]:
        print(line)
    print(f"-- {len(rows)} denial(s) recorded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
