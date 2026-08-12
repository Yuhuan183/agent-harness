#!/usr/bin/env python3
"""Recompute lifecycle-replay criteria 1 and 3 from retained artifacts. Reports.

`docs/research/lifecycle-replay.md` sets four criteria a replay result must meet
before it may be cited, and criterion 4 requires the first three to be
recomputable *by someone who did not run the session* — the runner's own account
does not count. That is the whole point, and it is also the constraint the
document does not yet satisfy: it assigns criterion 1 to a human, and a human's
say-so is exactly what criterion 4 refuses.

This closes that gap for the two criteria that generalise. Criterion 2 cannot
live here: a reach marker is per-scenario by construction, and the graders in
`evals/traps/*/grade.py` already recompute it from event streams.

**Criterion 1 — did the session end alive?** The transcript's shape answers it,
and the failure modes separate on real data (26 sessions, 96 subagents, surveyed
2026-08-12):

    assistant / end_turn   natural end
    user / interrupted     a human stopped it
    assistant / tool_use   ended with a tool call outstanding
    (no assistant record)  never produced a reply
    isCompactSummary       context ran out and the conversation was compacted

The last one matters most and is the easiest to overlook: a compacted session
did not hold its own run. Whether that disqualifies a replay is a judgement, but
it must be a *visible* judgement, so it is reported rather than folded into the
verdict.

**Criterion 3 — is every staged dispatch reconciled?** A stub whose dispatch id
the ledger never answered is unreconciled, which is what `weekly-integrity`
already watches. Repeated here so one command can produce the whole picture for
one session, and because the reconciliation is per-session while the hook's view
is global.

Exit status is always 0. A criterion that blocks would be a criterion people
route around; the document's own argument is that "nothing happened" data is
easy to fake and hard to withdraw, so the answer is to make it visible, not to
gate on it.

Usage:
    evals/scripts/lifecycle-criteria.py --session <id> [--json]
    evals/scripts/lifecycle-criteria.py --list
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"
PENDING = Path(os.environ.get(
    "AGENT_EXPERIENCE_PENDING",
    Path.home() / ".agents" / "telemetry" / "experience-pending.jsonl"))
LEDGER = Path(os.environ.get(
    "AGENT_EXPERIENCE_LEDGER",
    Path.home() / ".agents" / "telemetry" / "experience.jsonl"))


def records(path: Path):
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def transcripts(session: str) -> list[Path]:
    return sorted(PROJECTS.glob(f"*/{session}.jsonl"))


def criterion_1(path: Path) -> dict[str, object]:
    """How did this transcript end, and was context exhausted on the way?"""
    rows = list(records(path))
    compacted = any(row.get("isCompactSummary") for row in rows)
    ending, detail = "no-assistant", None
    for row in reversed(rows):
        if row.get("type") == "assistant":
            ending = "assistant"
            detail = (row.get("message") or {}).get("stop_reason")
            break
        if row.get("type") == "user":
            content = row.get("message", {}).get("content")
            text = content if isinstance(content, str) else json.dumps(
                content, ensure_ascii=False)
            ending = "user-interrupted" if "interrupted" in text.lower() else "user"
            break
    alive = ending == "assistant" and detail == "end_turn"
    return {"records": len(rows), "ending": ending, "stop_reason": detail,
            "compacted": compacted, "ended_alive": alive}


def criterion_3(session: str) -> dict[str, object]:
    """Staged dispatches for this session that the ledger never answered."""
    answered = {row.get("dispatch_id") for row in records(LEDGER)
                if row.get("dispatch_id")} if LEDGER.exists() else set()
    staged: dict[str, str] = {}
    if PENDING.exists():
        for row in records(PENDING):
            if row.get("session_id") != session:
                continue
            key = row.get("dispatch_id")
            if key:
                staged[key] = row.get("agent_type", "?")
    open_ids = sorted(key for key in staged if key not in answered)
    return {"staged": len(staged), "unreconciled": len(open_ids),
            "reconciled": all(key in answered for key in staged),
            "open": [{"dispatch_id": key, "agent_type": staged[key]}
                     for key in open_ids]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", help="session id to check")
    parser.add_argument("--list", action="store_true",
                        help="list session ids that have a transcript")
    parser.add_argument("--json", action="store_true", help="machine-readable")
    args = parser.parse_args()

    if args.list:
        for path in sorted(PROJECTS.glob("*/*.jsonl")):
            print(path.stem)
        return 0
    if not args.session:
        parser.error("--session is required (or use --list)")

    found = transcripts(args.session)
    if not found:
        print(f"no transcript for session {args.session}", file=sys.stderr)
        return 0

    report = {"session": args.session,
              "criterion_1": [dict(criterion_1(p), transcript=p.name)
                              for p in found],
              "criterion_3": criterion_3(args.session)}
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    print(f"session {args.session}")
    for entry in report["criterion_1"]:
        flag = "alive" if entry["ended_alive"] else "NOT alive"
        note = "  [compacted: context ran out]" if entry["compacted"] else ""
        print(f"  1 ended alive : {flag:<9} "
              f"({entry['ending']}/{entry['stop_reason']}, "
              f"{entry['records']} records){note}")
    third = report["criterion_3"]
    verdict = "reconciled" if third["reconciled"] else "NOT reconciled"
    print(f"  3 dispatches  : {verdict:<9} "
          f"({third['staged']} staged, {third['unreconciled']} unanswered)")
    for entry in third["open"]:
        print(f"      open  {entry['dispatch_id']}  ({entry['agent_type']})")
    print("  2 reach marker: per-scenario; see the trap's grade.py")
    print("  4 recomputable: this command is the recomputation for 1 and 3")
    return 0


if __name__ == "__main__":
    sys.exit(main())
