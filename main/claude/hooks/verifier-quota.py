#!/usr/bin/env python3
"""PreToolUse[Agent] gate: at most one outcome verifier per user prompt.

The rule in the contracts is per *top-level task*, and it is a judgment rule:
this gate enforces the part of it that a payload field can carry, which is one
verifier per prompt. Say that plainly rather than let the two be read as the
same thing (2026-07-29 review) — a reader who believes the gate is per-task
will trust it in exactly the case it does not cover.

The contracts have carried the rule as prose since the beginning, with nothing
able to refuse a second dispatch. "Distinct failure surfaces do not add quota"
is the part that makes it worth enforcing: the second verifier usually feels
justified at the time, which is exactly why the budget needs to be spent by a
mechanism rather than by judgment.

Carrier and its limit: a top-level task is a judgment boundary, not a field.
The closest thing the payload offers is `prompt_id` (a common field on every
hook payload, alongside `session_id` and `permission_mode`), so the quota
resets on each new user prompt. A task that spans prompts therefore gets a
fresh verifier per prompt — this under-enforces, never over-enforces, and the
alternative (keying on the session) would refuse a legitimate verifier for
every later task in a long session, which is the error that would teach people
to disarm the gate. Closing the gap needs a stable task id carried from the
orchestrator into the payload; nothing in the runtime offers one today, so the
gap is disclosed rather than papered over.

Spelling is the second limit, and it is provider-shaped. The quota keys on
`subagent_type`, so it counts the Claude `verifier` role and nothing else. The
documented route for a verdict that needs to run commands is a Codex `verifier`
reached through the `codex:codex-rescue` bridge, and that dispatch carries the
bridge's name rather than the role's — it spends no quota here. Listing the
bridge would refuse a second *implementation* dispatch in the same prompt,
since one name covers every Codex role and the payload has no field that
separates them. A cross-provider outcome verifier therefore stays a judgment
call, disclosed here and in the docs rather than half-enforced (2026-08-05
review).

Budget guard, not a safety boundary: if the payload carries no `prompt_id`
there is nothing to key on, and the dispatch proceeds with a note rather than
being blocked on a carrier this hook could not read. A run of such dispatches
means the field is gone rather than absent once, which would silently retire
the whole gate — the state file counts consecutive misses so weekly-integrity
can say so, and any dispatch that does carry the field clears the count.

Concurrency: this harness dispatches in parallel from one assistant message,
so two verifiers can reach the hook at the same instant. Read-check-write
without a lock lets both read an unspent quota and both proceed, which is the
one case the gate exists for — check and set therefore happen under an
exclusive lock on a sidecar, the same way experience-pending serializes its
appends.

Exit 0 allows; exit 2 blocks. Override a genuinely new task boundary inside
one prompt with AGENT_ALLOW_SECOND_VERIFIER=1.

Ordering: runtime-guard runs before this on PreToolUse[Agent], so a dispatch
blocked for an old runtime is rejected on the more fundamental ground first. A
version block on an old runtime also blocks every verifier, so the quota it
records cannot change an outcome there; the recording is a budget marker, not a
safety decision, and this ordering keeps the safety gate first.
"""
from __future__ import annotations

import json
import os
import sys
from contextlib import contextmanager

STATE = os.path.expanduser("~/.claude/telemetry/.verifier-quota.json")
OUTCOME_VERIFIERS = ("verifier",)
# Bookkeeping that is not a spent quota. The session prune below drops it along
# with every key outside this session, and that is the intent: a dispatch that
# carried `prompt_id` ends any run of misses, so the count belongs to the gap
# and not to the file. (This comment used to claim the opposite - that the key
# survived the prune - which is the reading that would make someone "fix" the
# prune into a permanent alarm; 2026-08-02 review.)
META_KEY = "_carrier"

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX falls back to no locking
    fcntl = None


@contextmanager
def quota_lock():
    """Serialize the whole check-and-set against a concurrent dispatch."""
    try:
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        handle = open(STATE + ".lock", "a", encoding="utf-8")
    except OSError:
        # No writable state directory: nothing to serialize against, and a
        # budget guard may not refuse a dispatch over its own bookkeeping.
        yield
        return
    try:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def load() -> dict:
    try:
        with open(STATE, encoding="utf-8") as fh:
            state = json.load(fh)
            return state if isinstance(state, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save(state: dict) -> None:
    try:
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        with open(STATE, "w", encoding="utf-8") as fh:
            json.dump(state, fh)
    except OSError:
        pass  # recording failed: allow, and let the next dispatch try again


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        return 0
    if payload.get("tool_name") != "Agent":
        return 0
    subagent = str((payload.get("tool_input") or {}).get("subagent_type", ""))
    if subagent not in OUTCOME_VERIFIERS:
        return 0
    if os.environ.get("AGENT_ALLOW_SECOND_VERIFIER") == "1":
        return 0

    session = str(payload.get("session_id", ""))
    prompt = payload.get("prompt_id")
    if not prompt:
        with quota_lock():
            spent = load()
            meta = spent.get(META_KEY) if isinstance(spent.get(META_KEY), dict) else {}
            misses = meta.get("misses", 0)
            misses = misses + 1 if isinstance(misses, int) else 1
            spent[META_KEY] = {"misses": misses}
            save(spent)
        print("[verifier-quota] no prompt_id in payload; the per-prompt quota is "
              f"not enforced for this dispatch (consecutive: {misses})",
              file=sys.stderr)
        return 0

    key = f"{session}:{prompt}"
    with quota_lock():
        spent = load()
        if key in spent:
            print(
                "[verifier-quota] blocked: this prompt already spent its outcome "
                f"verifier ({spent[key]}). Distinct failure surfaces do not add "
                "quota — verify at the smallest coherent integration boundary "
                "instead of stacking gates. If this really is a new top-level "
                "task, re-dispatch with AGENT_ALLOW_SECOND_VERIFIER=1.",
                file=sys.stderr)
            return 2

        spent[key] = payload.get("tool_use_id") or "dispatched"
        # Keep only this session's keys; the file is a budget, not a ledger.
        # The carrier arrived, so any earlier run of misses is over.
        spent = {k: v for k, v in spent.items() if k.startswith(f"{session}:")}
        save(spent)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
