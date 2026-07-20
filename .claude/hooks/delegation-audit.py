#!/usr/bin/env python3
"""Delegation audit hook: append SubagentStart/SubagentStop events to
~/.claude/telemetry/delegation.jsonl. Fail-open by design — any error
exits 0 so monitoring can never block work."""
import json
import os
import sys
from datetime import datetime, timezone


def spawn_depth(ev):
    # <transcripts>/<session_id>.jsonl -> <transcripts>/<session_id>/subagents/agent-<id>.meta.json
    tp, aid = ev.get("transcript_path"), ev.get("agent_id")
    if not (tp and aid):
        return None
    meta = os.path.join(tp[:-6] if tp.endswith(".jsonl") else tp,
                        "subagents", f"agent-{aid}.meta.json")
    try:
        return json.load(open(meta)).get("spawnDepth")
    except Exception:
        return None


try:
    ev = json.load(sys.stdin)
    depth = spawn_depth(ev)
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "event": ev.get("hook_event_name"),
        "agent_type": ev.get("agent_type"),
        "agent_id": ev.get("agent_id"),
        "session_id": ev.get("session_id"),
        "spawn_depth": depth,
    }
    # depth >= 2 means a subagent spawned another subagent — forbidden for role
    # agents. meta.json is written after spawn, so this lands on the Stop event.
    if depth is not None and depth >= 2:
        rec["nested"] = True
    out = os.path.expanduser("~/.claude/telemetry/delegation.jsonl")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "a") as f:
        f.write(json.dumps(rec) + "\n")
except Exception:
    pass
sys.exit(0)
