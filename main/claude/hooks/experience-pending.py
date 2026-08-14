#!/usr/bin/env python3
"""Experience-ledger pending hook.

On SubagentStart/SubagentStop, stage a pending dispatch stub (agent_type,
wall-clock secs, token usage) so the main session can log an outcome with
`experience-log --from-pending --outcome <o>` instead of retyping
role/tier/secs/tokens.

On Stop, sweep dispatches that nobody ever judged into the ledger as
`outcome=unjudged`. Replay measured that step failing in 18 of 33 sessions on
2026-08-14, in three shapes, of which only one was reachable by better tooling:
three of five sessions never invoked `experience-log` at all, and no message
printed by a command changes the behaviour of a session that does not run it.
A manual step that fails more than half the time is a design problem rather
than a discipline one, so the fact gets recorded instead of the row going
missing.

Two rules keep the sweep from doing harm, and the first is the important one:

1. **Never sweep the current session.** `Stop` fires at the end of every
   assistant turn, not only at session end, so a sweep of one's own stubs would
   file `unjudged` for a dispatch about to be judged one turn later — and
   `experience-log` refuses a second record for the same dispatch, which would
   make things worse than the silence. Another session's `Stop` sweeps yours.
2. **An age floor on top**, because sessions run concurrently and one may still
   be working.

`unjudged` is terminal by construction: the session that made the dispatch has
ended. It is excluded from routing decisions for free — `decision_eligible`
requires one of the four judged outcomes and skips otherwise, so the record
lands in `ineligible_n` and touches no denominator.

Fail-open throughout — any error exits 0."""
import json
import os
import sys
from contextlib import contextmanager
from datetime import datetime, timezone

PENDING = os.environ.get(
    "AGENT_EXPERIENCE_PENDING",
    os.path.expanduser("~/.agents/telemetry/experience-pending.jsonl"),
)
LEDGER = os.environ.get(
    "AGENT_EXPERIENCE_LEDGER",
    os.path.expanduser("~/.agents/telemetry/experience.jsonl"),
)
# Overridable so the sweep can be exercised against a temp ledger without the
# test depending on what happens to be deployed.
EXPERIENCE_LOG = os.environ.get(
    "AGENT_EXPERIENCE_LOG_BIN",
    os.path.expanduser("~/.agents/skills/experience-ledger/scripts/experience-log"))
# Long enough that a concurrent session doing slow work is not pre-empted, short
# enough that the record lands the same day. The rule that actually prevents
# pre-emption is "never your own session"; this is the second guard, not the
# first.
SWEEP_MIN_AGE_SECS = 3600

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

    A damaged row costs one row, not the scan. The hook is fail-open, so an
    uncaught UnicodeDecodeError here did not crash anything visibly - it fell
    through to the outer `except Exception` and returned exit 0 having written
    no stub at all, so every later dispatch lost its completion carrier in
    silence (2026-07-31 re-review).
    """
    records = []
    try:
        with open(PENDING, encoding="utf-8", errors="replace") as f:
            for raw in f:
                if not raw.strip():
                    continue
                try:
                    row = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                # `[]`, `"junk"`, `42` and `null` are all valid JSON and all
                # blow up on the first `.get()`. Skipping only malformed JSON
                # left that whole class live: an AttributeError here still fell
                # through to the outer `except Exception`, still exited 0, and
                # still wrote no stub (2026-07-31 re-review, second pass).
                if isinstance(row, dict):
                    records.append(row)
    except OSError:
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



def sweep_unjudged(current_session, now):
    """File `unjudged` for other sessions' dispatches the ledger never answered.

    Delegates the write to `experience-log` rather than appending here: that
    script owns the schema, the route resolution, the one-record-per-dispatch
    rule and the lock ordering, and a second writer that knew half of them is
    how a ledger stops being readable. Returns the ids it swept, for the tests.
    """
    import subprocess

    answered = set()
    try:
        with open(LEDGER, encoding="utf-8", errors="replace") as stream:
            for raw in stream:
                if not raw.strip():
                    continue
                try:
                    row = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if isinstance(row, dict) and row.get("dispatch_id"):
                    answered.add(row["dispatch_id"])
    except OSError:
        pass

    stale = {}
    try:
        with open(PENDING, encoding="utf-8", errors="replace") as stream:
            for raw in stream:
                if not raw.strip():
                    continue
                try:
                    row = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if not isinstance(row, dict) or row.get("event") != "SubagentStop":
                    continue
                key = row.get("dispatch_id")
                if not key or key in answered:
                    continue
                if row.get("session_id") == current_session:
                    continue                      # never your own, see module docstring
                try:
                    when = datetime.fromisoformat(row.get("ts", ""))
                except (TypeError, ValueError):
                    continue
                if (now - when).total_seconds() < SWEEP_MIN_AGE_SECS:
                    continue
                stale[key] = row
    except OSError:
        return []

    swept = []
    for key in sorted(stale):
        done = subprocess.run(
            [sys.executable, EXPERIENCE_LOG, "--from-pending",
             "--dispatch-id", key, "--outcome", "unjudged",
             "--note", "swept at session end; no outcome was ever logged"],
            capture_output=True, text=True, timeout=30)
        if done.returncode == 0:
            swept.append(key)
    return swept

try:
    ev = json.load(sys.stdin)
    now = datetime.now(timezone.utc)
    if ev.get("hook_event_name") == "Stop":
        sweep_unjudged(ev.get("session_id"), now)
        sys.exit(0)
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
