#!/usr/bin/env python3
"""Experience-ledger pending hook: on SubagentStart/SubagentStop, stage a
pending dispatch stub (agent_type, wall-clock secs, output tokens) so the
main session can log an outcome with `experience-log --from-pending
--outcome <o>` instead of retyping role/tier/secs/tokens. Fail-open — any
error exits 0."""
import json
import os
import sys
from datetime import datetime, timezone

PENDING = os.environ.get(
    "AGENT_EXPERIENCE_PENDING",
    os.path.expanduser("~/.agents/telemetry/experience-pending.jsonl"),
)

def sum_output_tokens(transcript_path, agent_id):
    """Sum output_tokens across the subagent's assistant turns, deduped by
    message id (streaming may append several snapshots of one message)."""
    base = transcript_path[:-6] if transcript_path.endswith(".jsonl") else transcript_path
    path = os.path.join(base, "subagents", f"agent-{agent_id}.jsonl")
    per_message = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    msg = json.loads(line).get("message") or {}
                    tokens = (msg.get("usage") or {}).get("output_tokens")
                    if isinstance(tokens, int):
                        per_message[msg.get("id") or len(per_message)] = tokens
                except (json.JSONDecodeError, AttributeError):
                    continue
    except OSError:
        return None
    return sum(per_message.values()) or None


def latest_matching_start(agent_id, session_id, stop_time):
    """Return the newest start for this exact dispatch before the stop.

    Agent ids are not assumed to be globally unique across sessions.
    """
    try:
        with open(PENDING, encoding="utf-8") as f:
            records = [json.loads(line) for line in f if line.strip()]
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    for prev in reversed(records):
        if (prev.get("event") != "SubagentStart"
                or prev.get("agent_id") != agent_id
                or prev.get("session_id") != session_id):
            continue
        try:
            start = datetime.fromisoformat(prev["ts"])
        except (KeyError, ValueError, TypeError):
            continue
        if start <= stop_time:
            return start
    return None


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
        # Measure subagent runtime only. Match session as well as agent id so
        # overlapping sessions cannot lend each other a start timestamp.
        start = latest_matching_start(rec["agent_id"], rec["session_id"], now)
        if start is not None:
            rec["secs"] = round((now - start).total_seconds(), 1)
        if ev.get("transcript_path"):
            tokens = sum_output_tokens(ev["transcript_path"], rec["agent_id"])
            if tokens is not None:
                rec["tokens_out"] = tokens
    os.makedirs(os.path.dirname(PENDING), exist_ok=True)
    with open(PENDING, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
except Exception:
    pass
sys.exit(0)
