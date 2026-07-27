#!/usr/bin/env python3
"""SessionStart[source=compact] re-seed for Claude Code.

PreCompact cannot shape the compaction summary - it can only veto compaction or
run a side effect, never add to or steer what the summary keeps (verified
against the hooks reference, 2026-07). So "before compacting, preserve the
goal, decisions in flight, and open items" cannot be a compaction-time gate.

SessionStart fires again *after* compaction with source="compact" and is one of
the few events whose additionalContext is injected into context. This delivers
that reminder once, deterministically, at exactly that boundary - turning "hope
the model compacted carefully" into a mechanism for *when* the reminder appears.
The content stays the model's judgment; only its timing is mechanized.

Fail-open: malformed input, the wrong event, or any internal error exits 0 with
no output. It only injects a reminder and must never block a session starting.
"""
import json
import sys

REMINDER = (
    "Context was just compacted. Before continuing, restate in one place the "
    "current goal, every decision still in flight (each as a `DECISION:` line), "
    "and any open or unfinished items, in case the summary dropped them."
)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    if payload.get("hook_event_name") != "SessionStart":
        return 0
    if payload.get("source") != "compact":
        return 0
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": REMINDER,
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
