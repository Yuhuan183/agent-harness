#!/usr/bin/env python3
"""PreToolUse[Agent] gate: at most one outcome verifier per top-level task.

The contracts have carried this rule as prose since the beginning, with
nothing able to refuse a second dispatch. "Distinct failure surfaces do not
add quota" is the part that makes it worth enforcing: the second verifier
usually feels justified at the time, which is exactly why the budget needs to
be spent by a mechanism rather than by judgment.

Carrier and its limit: a top-level task is a judgment boundary, not a field.
The closest thing the payload offers is `prompt_id`, so the quota resets on
each new user prompt. A task that spans prompts therefore gets a fresh
verifier per prompt — this under-enforces, never over-enforces, and the
alternative (keying on the session) would refuse a legitimate verifier for
every later task in a long session.

Budget guard, not a safety boundary: if the payload carries no `prompt_id`
there is nothing to key on, and the dispatch proceeds with a note rather than
being blocked on a carrier this hook could not read.

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

STATE = os.path.expanduser("~/.claude/telemetry/.verifier-quota.json")
OUTCOME_VERIFIERS = ("verifier",)


def load() -> dict:
    try:
        with open(STATE, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}


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

    prompt = payload.get("prompt_id")
    if not prompt:
        print("[verifier-quota] no prompt_id in payload; per-task quota not "
              "enforced for this dispatch", file=sys.stderr)
        return 0
    key = f"{payload.get('session_id', '')}:{prompt}"

    spent = load()
    if key in spent:
        print(
            "[verifier-quota] blocked: this task already spent its outcome "
            f"verifier ({spent[key]}). Distinct failure surfaces do not add "
            "quota — verify at the smallest coherent integration boundary "
            "instead of stacking gates. If this really is a new top-level "
            "task, re-dispatch with AGENT_ALLOW_SECOND_VERIFIER=1.",
            file=sys.stderr)
        return 2

    spent[key] = payload.get("tool_use_id") or "dispatched"
    try:
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        # Keep only this session's keys; the file is a budget, not a ledger.
        session = str(payload.get("session_id", ""))
        spent = {k: v for k, v in spent.items() if k.startswith(f"{session}:")}
        with open(STATE, "w", encoding="utf-8") as fh:
            json.dump(spent, fh)
    except OSError:
        pass  # recording failed: allow, and let the next dispatch try again
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
