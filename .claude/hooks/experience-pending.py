#!/usr/bin/env python3
"""Experience-ledger pending hook: on SubagentStart/SubagentStop, stage a
pending dispatch stub (agent_type, wall-clock secs) so the main session can
log an outcome with `experience-log --from-pending --outcome <o>` instead of
retyping role/tier/secs. Fail-open — any error exits 0."""
import json
import os
import sys
from datetime import datetime, timezone

PENDING = os.environ.get(
    "AGENT_EXPERIENCE_PENDING",
    os.path.expanduser("~/.agents/telemetry/experience-pending.jsonl"),
)

try:
    ev = json.load(sys.stdin)
    now = datetime.now(timezone.utc)
    rec = {
        "ts": now.isoformat(timespec="seconds"),
        "event": ev.get("hook_event_name"),
        "agent_type": ev.get("agent_type"),
        "agent_id": ev.get("agent_id"),
        "session_id": ev.get("session_id"),
    }
    if rec["event"] == "SubagentStop" and rec["agent_id"]:
        # pair with the staged start to compute dispatch wall-clock
        try:
            with open(PENDING, encoding="utf-8") as f:
                for line in f:
                    prev = json.loads(line)
                    if (prev.get("event") == "SubagentStart"
                            and prev.get("agent_id") == rec["agent_id"]):
                        start = datetime.fromisoformat(prev["ts"])
                        rec["secs"] = round((now - start).total_seconds(), 1)
        except FileNotFoundError:
            pass
    os.makedirs(os.path.dirname(PENDING), exist_ok=True)
    with open(PENDING, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
except Exception:
    pass
sys.exit(0)
