#!/usr/bin/env python3
"""Experience-ledger pending hook: on SubagentStart/SubagentStop, stage a
pending dispatch stub (agent_type, wall-clock secs, token usage) so the
main session can log an outcome with `experience-log --from-pending
--outcome <o>` instead of retyping role/tier/secs/tokens. Fail-open — any
error exits 0."""
import json
import os
import sys
from contextlib import contextmanager
from datetime import datetime, timezone

PENDING = os.environ.get(
    "AGENT_EXPERIENCE_PENDING",
    os.path.expanduser("~/.agents/telemetry/experience-pending.jsonl"),
)

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX fallback remains fail-open
    fcntl = None


@contextmanager
def pending_lock():
    """Serialize appends with experience-log's read/modify/write cycle."""
    os.makedirs(os.path.dirname(PENDING), exist_ok=True)
    with open(PENDING + ".lock", "a", encoding="utf-8") as lock:
        if fcntl is not None:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

USAGE_FIELDS = {
    "input_tokens": "tokens_in",
    "output_tokens": "tokens_out",
    "cache_creation_input_tokens": "cache_write_tokens",
    "cache_read_input_tokens": "cache_read_tokens",
}


def subagent_telemetry(transcript_path, agent_id):
    """Token usage and the model Claude recorded, from one transcript pass.

    Usage is summed across assistant turns and deduped by message id, because
    streaming may append several snapshots of one message and the latest usage
    object replaces the earlier ones.

    Each assistant turn also carries the model that produced it. That is
    Claude's own account of the route it ran — the Claude-side counterpart of
    a Codex rollout's `thread_settings_applied`, and the only route evidence on
    this side that does not come from the dispatcher. Effort has no such
    record: on Claude it is the frontmatter pin, not a provider-reported fact.
    """
    base = transcript_path[:-6] if transcript_path.endswith(".jsonl") else transcript_path
    path = os.path.join(base, "subagents", f"agent-{agent_id}.jsonl")
    per_message = {}
    models = set()
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    msg = json.loads(line).get("message") or {}
                    usage = msg.get("usage") or {}
                    if any(isinstance(usage.get(field), int) for field in USAGE_FIELDS):
                        per_message[msg.get("id") or len(per_message)] = usage
                    model = msg.get("model")
                    # `<synthetic>` marks a turn Claude Code produced locally
                    # (API errors, interrupts). It names no model, so counting
                    # it would turn a normal dispatch into a two-model one.
                    if isinstance(model, str) and model and not model.startswith("<"):
                        models.add(model)
                except (json.JSONDecodeError, AttributeError):
                    continue
    except OSError:
        return {}
    totals = {}
    for source, target in USAGE_FIELDS.items():
        values = [usage.get(source) for usage in per_message.values()]
        if any(isinstance(value, int) for value in values):
            totals[target] = sum(value for value in values if isinstance(value, int))
    if len(models) == 1:
        totals["observed_model"] = models.pop()
    elif len(models) > 1:
        # A dispatch that ran on more than one model has no single route to
        # attest, the same way an ambiguous rollout window attests nothing.
        totals["telemetry_warning"] = "ambiguous_transcript_model"
    return totals


CODEX_SESSIONS = os.environ.get(
    "CODEX_SESSIONS_DIR", os.path.expanduser("~/.codex/sessions"))


def codex_route_from_rollout(path):
    """Return the model/effort Codex itself recorded for this rollout.

    The bridge job sidecar stores no route, so a bridge record's route would
    otherwise be the dispatcher's self-report. Codex writes the applied thread
    settings into the rollout, which is the provider-recorded telemetry the
    provider-extension protocol requires of every routable target.
    """
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if '"thread_settings_applied"' not in line:
                    continue
                settings = (json.loads(line).get("payload") or {}).get(
                    "thread_settings") or {}
                model = settings.get("model")
                effort = settings.get("reasoning_effort")
                if model and effort:
                    return {"observed_model": model, "observed_effort": effort}
    except (OSError, json.JSONDecodeError, AttributeError, TypeError):
        pass
    return {}


def codex_usage_tokens(start, stop):
    """Token delta for one unambiguous Codex rollout in [start, stop].

    A codex-bridge subagent's own transcript only shows the thin forwarder;
    the real usage lands in ~/.codex/sessions rollouts. Delta against the
    last pre-start snapshot keeps resumed threads from over-counting.
    """
    import glob
    candidates = []
    for path in glob.glob(os.path.join(CODEX_SESSIONS, "*/*/*/rollout-*.jsonl")):
        try:
            if datetime.fromtimestamp(os.path.getmtime(path), timezone.utc) < start:
                continue
            baseline, final = None, None
            with open(path, encoding="utf-8") as f:
                for line in f:
                    if '"token_count"' not in line:
                        continue
                    try:
                        entry = json.loads(line)
                        ts = datetime.fromisoformat(
                            entry["timestamp"].replace("Z", "+00:00"))
                        usage = entry["payload"]["info"]["total_token_usage"]
                    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
                        continue
                    if ts < start:
                        baseline = usage
                    elif ts <= stop:
                        final = usage
            if final is None:
                continue
            base = baseline or {}
            delta = {
                field: max(0, final.get(field, 0) - base.get(field, 0))
                for field in ("input_tokens", "cached_input_tokens", "output_tokens")
            }
            if any(delta.values()):
                candidates.append((path, delta))
        except OSError:
            continue
    if not candidates:
        return {}
    if len(candidates) > 1:
        return {
            "telemetry_warning": "ambiguous_codex_rollout",
            "rollout_candidates": len(candidates),
        }
    path, totals = candidates[0]
    return {
        "tokens_in": max(
            0, totals.get("input_tokens", 0) - totals.get("cached_input_tokens", 0)
        ),
        "cache_read_tokens": totals.get("cached_input_tokens", 0),
        "tokens_out": totals.get("output_tokens", 0),
        "rollout_id": os.path.basename(path).removesuffix(".jsonl"),
        # Same unambiguous rollout, so the route is attested by the same
        # evidence as the tokens. An ambiguous window returns above without
        # either: a rollout that cannot be pinned cannot attest a route.
        **codex_route_from_rollout(path),
    }


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
    # Claude emits system-managed spawns without an agent type. They are not
    # one of this harness's dispatches and would otherwise block --from-pending.
    if not rec["agent_type"]:
        sys.exit(0)
    rec["dispatch_id"] = f"{rec['session_id']}:{rec['agent_id']}"
    rec["request_source"] = (
        "claude-code-plugin-codex"
        if "codex" in rec["agent_type"].lower()
        else "claude-code"
    )
    if rec["event"] == "SubagentStop" and rec["agent_id"]:
        # Measure subagent runtime only. Match session as well as agent id so
        # overlapping sessions cannot lend each other a start timestamp.
        start = latest_matching_start(rec["agent_id"], rec["session_id"], now)
        if start is not None:
            rec["secs"] = round((now - start).total_seconds(), 1)
        if "codex" in rec["agent_type"].lower():
            # Bridge dispatch: the Claude transcript only carries the thin
            # forwarder; pull the real usage from the Codex rollouts.
            if start is not None:
                rec.update(codex_usage_tokens(start, now))
        elif ev.get("transcript_path"):
            rec.update(subagent_telemetry(ev["transcript_path"], rec["agent_id"]))
    with pending_lock():
        with open(PENDING, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
except Exception:
    pass
sys.exit(0)
