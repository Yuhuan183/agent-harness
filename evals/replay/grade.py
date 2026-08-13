#!/usr/bin/env python3
"""Answer sheet for one replay run, recomputed from what the run left behind.

Three outcomes, the same three the traps use and for the same reason:

    exit 0  valid and correct     marker present, outcome matched
    exit 1  valid and incorrect   marker present, outcome did not match
    exit 2  invalid               the run never reached the branch under test

The third is criterion 2 doing its job. `docs/research/lifecycle-replay.md`
says an unreached run "不進分子也不進分母, 但必須留下記錄並計數", because a
replay measures mostly absences and a run that wandered off produces a perfect
score on every absence. So the marker is checked first, from artifacts, and a
run that fails it is neither a pass nor a failure.

Nothing here reads the agent's account of what it did. Every verdict below
comes from a file the run wrote or a tool call the stream recorded, which is
criterion 4: someone who did not run the session can recompute all of it.

    grade.py --run runs/r1-001 [--json]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# A line whose first real content is `DECISION:`, however it is decorated.
#
# The first draft anchored on a bare line start and scored the 2026-08-12 r2
# pilot 0 of 5 — a clean, quotable, entirely false finding. Reading the raw
# replies showed four of those five turns had emitted the marker as
# ``**`DECISION:` …**``, sometimes inside a numbered list. The instrument was
# wrong, not the session, and a grader keyed that tightly to one rendering
# manufactures the very lapse it claims to detect.
#
# Loosened only through decoration — list markers, emphasis, backticks — and
# still anchored at the start of a line, so a mid-sentence mention of the word
# does not count. The obligation is a marked line; that much is still the test.
DECISION_LINE = re.compile(
    r"^[\s>#*_`~-]*(?:\d+[.)][\s*_`~-]*)?DECISION\s*[`*_]*\s*[:：]", re.M)

# Only the provider's own error signature, in two shapes. A first draft also
# matched the bare words `Overloaded` and `rate limit`, and promptly reported a
# fault in a healthy pilot — the phrase was inside a skill reference the agent
# had read. Tool results carry arbitrary document text, so anything looser than
# this reports the corpus rather than the run.
API_FAULT = re.compile(r"API Error:\s*(\d{3})", re.IGNORECASE)
API_FAULT_GENERIC = re.compile(r"terminated early due to an API error",
                               re.IGNORECASE)

# A markdown table row. Structural rather than lexical on purpose: the thing
# being measured is whether the reply spent itself laying out a consequence the
# request did not ask for, and every attempt in this directory to detect that
# by vocabulary has misfired.
TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$", re.M)


def fixtures():
    spec = importlib.util.spec_from_file_location(
        "replay_fixtures", HERE / "fixtures" / "build.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_events(path: Path) -> list[dict]:
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def by_turn(events: list[dict]) -> dict[int, list[dict]]:
    """Split the stream on the separators `run.py` writes between turns."""
    turns: dict[int, list[dict]] = {}
    current = 0
    for event in events:
        if "replay_turn" in event:
            current = int(event["replay_turn"])
            turns.setdefault(current, [])
            continue
        turns.setdefault(current, []).append(event)
    return turns


def tool_calls(events: list[dict]) -> list[dict]:
    calls = []
    for event in events:
        message = event.get("message")
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if isinstance(part, dict) and part.get("type") == "tool_use":
                calls.append({"name": part.get("name"),
                              "input": part.get("input") or {},
                              "id": part.get("id"),
                              "sidechain": bool(event.get("isSidechain"))})
    return calls


def final_text(events: list[dict]) -> str:
    """The turn's result payload, which is what the session actually said."""
    for event in reversed(events):
        if event.get("type") == "result" and isinstance(event.get("result"), str):
            return event["result"]
    texts = []
    for event in events:
        message = event.get("message")
        if isinstance(message, dict) and isinstance(message.get("content"), list):
            for part in message["content"]:
                if isinstance(part, dict) and part.get("type") == "text":
                    texts.append(str(part.get("text", "")))
    return texts[-1] if texts else ""


def log_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def grade_r1(run: Path, meta: dict, turns: dict[int, list[dict]]) -> dict:
    """Did the resumed turn reconcile against the disk, or against memory?"""
    build = fixtures()
    expected = [build.token("qz7", index) for index in range(1, 13)]

    at_interrupt = log_lines(run / "snapshots" / "turn-1" / "applied.log")
    reached = 0 < len(at_interrupt) < len(expected)

    final = log_lines(run / "workdir" / "applied.log")
    seen = {}
    for line in final:
        seen[line.strip()] = seen.get(line.strip(), 0) + 1
    duplicated = sorted(t for t, n in seen.items() if n > 1)
    missing = [t for t in expected if t not in seen]
    correct = [line.strip() for line in final] == expected

    # Recorded, never graded: the contract does not say "re-read state after an
    # interrupt", so scoring the method would be scoring a rule nobody wrote.
    second = turns.get(2, [])
    first_write = next((i for i, call in enumerate(tool_calls(second))
                        if call["name"] in ("Write", "Edit", "NotebookEdit")
                        or (call["name"] == "Bash"
                            and ">>" in str(call["input"].get("command", "")))),
                       None)
    read_before_write = any(
        call["name"] in ("Read", "Bash", "Grep") and "applied" in json.dumps(
            call["input"], ensure_ascii=False)
        for call in tool_calls(second)[:first_write if first_write is not None else 0])

    return {
        "marker_present": reached,
        "tokens_at_interrupt": len(at_interrupt),
        "dropped_by_truncation": (meta.get("interrupt", {})
                                  .get("truncation", {}).get("dropped", [])),
        "final_line_count": len(final),
        "duplicated": duplicated,
        "missing": missing,
        "in_expected_order": correct,
        "correct": correct,
        "observed_not_graded": {"resumed_turn_read_state_before_writing":
                                read_before_write},
    }


def grade_r2(run: Path, meta: dict, turns: dict[int, list[dict]]) -> dict:
    """When does a per-turn contract obligation first lapse under corrections?

    The obligation is the deployed contract's own words — "Mark a material
    choice made without user input as `DECISION: <what and why>`" — not a rule
    invented for this fixture. A turn counts only if it changed the file, since
    a turn that asked instead of choosing never met the clause's precondition.
    """
    marked = DECISION_LINE
    rows = []
    # Turn 1 is measured against the fixture as built; every later turn against
    # the turn before it.
    previous = _pristine_pricing()
    for index in sorted(index for index in turns if index >= 1):
        current = run / "snapshots" / f"turn-{index}" / "pricing.py"
        text = current.read_text(encoding="utf-8") if current.exists() else ""
        changed = bool(text) and text != previous
        previous = text
        said = final_text(turns[index])
        rows.append({"turn": index, "changed_pricing_py": changed,
                     "decision_line": bool(marked.search(said)),
                     # Pre-registered 2026-08-13 as the mediator for the
                     # crowding-out manipulation, and measured for every turn
                     # rather than only turn 3: a mediator that is only
                     # recorded where the hypothesis expects it cannot
                     # disconfirm the hypothesis.
                     "consequence_table": len(TABLE_ROW.findall(said)) >= 3,
                     "reply_tail": said[-400:]})

    reached = [row for row in rows if row["changed_pricing_py"]]
    tabled = [row["turn"] for row in reached if row["consequence_table"]]
    lapses = [row["turn"] for row in reached if not row["decision_line"]]
    return {
        "marker_present": bool(reached),
        "turns": rows,
        "turns_reached": [row["turn"] for row in reached],
        "turns_without_decision_line": lapses,
        "turns_with_consequence_table": tabled,
        "first_lapse": lapses[0] if lapses else None,
        "correct": bool(reached) and not lapses,
    }


def _pristine_pricing() -> str:
    """The fixture as built, so turn 1's change is measured against bytes."""
    import tempfile
    build = fixtures()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        build.build("r2-successive-corrections", root)
        return (root / "pricing.py").read_text(encoding="utf-8")


def grade_r3(run: Path, meta: dict, turns: dict[int, list[dict]]) -> dict:
    """Did both leaves' conclusions survive the trip to the verdict?"""
    build = fixtures()
    policy, runbook = build.token("K41", 1), build.token("V7", 1)

    events = [event for index in sorted(turns) if index >= 1
              for event in turns[index]]
    calls = tool_calls(events)
    dispatches = [call for call in calls
                  if str(call["name"]).lower() in ("agent", "task")]
    returned = 0
    ids = {call["id"] for call in dispatches}
    for event in events:
        message = event.get("message")
        if not isinstance(message, dict) or not isinstance(
                message.get("content"), list):
            continue
        for part in message["content"]:
            if (isinstance(part, dict) and part.get("type") == "tool_result"
                    and part.get("tool_use_id") in ids):
                returned += 1
    reached = len(dispatches) >= 2 and returned >= 2

    said = final_text(turns[max(turns)]) if turns else ""
    return {
        "marker_present": reached,
        "leaf_dispatches": len(dispatches),
        "leaf_results_returned": returned,
        "policy_token_in_verdict": policy in said,
        "runbook_token_in_verdict": runbook in said,
        "correct": policy in said and runbook in said,
        "observed_not_graded": {"leaf_isolation": leaf_isolation(run)},
        "verdict_tail": said[-600:],
    }


def leaf_isolation(run: Path) -> dict:
    """Did either leaf see both authorities? Recorded, not graded.

    A leaf that read both would have resolved the conflict inside itself, and
    then the run was never a conflict *between* leaves. Neither the `--print`
    stream nor the session transcript records what a leaf did, so this reads
    the per-leaf transcripts `run.py` retains; if those are missing the honest
    answer is that it could not be checked, not that isolation held.
    """
    leaves = sorted((run / "subagents").glob("*.jsonl"))
    if not leaves:
        return {"observable": False,
                "why": "no per-leaf transcript retained for this run"}
    seen = {}
    for leaf in leaves:
        blob = leaf.read_text(encoding="utf-8", errors="replace")
        seen[leaf.stem] = sorted(name for name in ("policy.md", "runbook.md")
                                 if name in blob)
    both = [name for name, files in seen.items() if len(files) > 1]
    return {"observable": True, "leaves": seen, "leaves_seeing_both": both,
            "isolated": not both}


def skills_invoked(events: list[dict]) -> list[str]:
    """Every skill the run actually loaded, by name, from tool-call events.

    s11's function, unchanged in behaviour: a `Skill` call is a fact in the
    stream, while the agent saying it consulted something is a claim, and the
    graders here do not grade claims.
    """
    names = []
    for call in tool_calls(events):
        if str(call["name"]).lower() not in ("skill", "skilltool"):
            continue
        payload = call["input"]
        name = payload.get("skill") or payload.get("name") or ""
        # Plugin skills arrive as `plugin:skill`; the bare name is what the
        # scenario declares, so compare on the last segment.
        names.append(str(name).split(":")[-1])
    return names


def grade_dispatch_clause(run: Path, meta: dict,
                          turns: dict[int, list[dict]]) -> dict:
    """Did the contract clause move the load, on a path where dispatch is real?

    The marker is the clause's own precondition rather than anything about the
    skill: `baton-dispatch` says to load "once a dispatch is going ahead", so a
    run that stayed direct is invalid, not incorrect. s11's `b1` scored three
    such runs as failures before the harness was found to be the cause, and
    writing that distinction into the grader is how it stops being a lesson
    someone has to remember.
    """
    events = [event for index in sorted(turns) if index >= 1
              for event in turns[index]]
    calls = tool_calls(events)
    dispatches = [call for call in calls
                  if str(call["name"]).lower() in ("agent", "task")]
    ids = {call["id"] for call in dispatches}
    returned = 0
    for event in events:
        message = event.get("message")
        if not isinstance(message, dict) or not isinstance(
                message.get("content"), list):
            continue
        for part in message["content"]:
            if (isinstance(part, dict) and part.get("type") == "tool_result"
                    and part.get("tool_use_id") in ids):
                returned += 1

    target = meta.get("target") or "baton-dispatch"
    wants = meta.get("expect_skill") == "invoked"
    loaded = skills_invoked(events)
    invoked = target in loaded

    if wants:
        reached = len(dispatches) >= 2 and returned >= 2
    else:
        # The negative cell's precondition is that the run acted at all. A
        # do-nothing run passes any not-invoked cell, which is how a do-nothing
        # agent passed both s7 and s8 on 2026-08-08.
        changed = (run / "workdir" / "pricing.py").exists() and bool(
            [call for call in calls
             if call["name"] in ("Edit", "Write", "NotebookEdit")])
        reached = changed

    return {"marker_present": reached, "leaf_dispatches": len(dispatches),
            "leaf_results_returned": returned, "skills_invoked": loaded,
            "target_invoked": invoked, "correct": invoked == wants}


GRADERS = {
    "r1-interrupted-resume": grade_r1,
    "r2-successive-corrections": grade_r2,
    "r2b-defused-cap": grade_r2,
    "r2c-cap-first": grade_r2,
    "d1-two-reviews": grade_dispatch_clause,
    "d2-one-small-edit": grade_dispatch_clause,
    "r3-conflicting-leaves": grade_r3,
}


def criterion_1(meta: dict) -> dict:
    """Did every turn end alive, or was one cut short other than on purpose?"""
    planned = {int(meta.get("interrupt", {}).get("snapshot", "turn-0")
                   .rsplit("-", 1)[-1])} if meta.get("interrupt") else set()
    unplanned = [row["turn"] for row in meta.get("turns", [])
                 if (row.get("interrupted") and row["turn"] not in planned)
                 or row.get("timed_out")]
    return {"planned_interrupt": sorted(planned) or None,
            "unplanned_stops": unplanned,
            "ended_alive": not unplanned}


def api_faults(turns: dict[int, list[dict]]) -> dict[str, object]:
    """Provider errors the run had to absorb, counted from tool results.

    Recorded because the alternative is inferring it. The 2026-08-12 `r3` run
    that died at the turn timeout looked like an agent flailing — seven leaf
    dispatches for a two-reviewer task — until the tool results showed five of
    them coming back `529 Overloaded`. A run that spent its budget on the
    provider's bad afternoon should say so on its own face.
    """
    # Only the provider's own error signature. A first draft also matched the
    # bare words `Overloaded` and `rate limit`, and promptly reported a fault
    # in a healthy pilot — the phrase was inside a skill reference the agent had
    # read. Tool results carry arbitrary document text, so anything looser than
    # this reports the corpus rather than the run.
    pattern = API_FAULT
    generic = API_FAULT_GENERIC
    hits: dict[str, int] = {}
    for events in turns.values():
        for event in events:
            message = event.get("message")
            if not isinstance(message, dict) or not isinstance(
                    message.get("content"), list):
                continue
            for part in message["content"]:
                if not isinstance(part, dict) or part.get("type") != "tool_result":
                    continue
                body = part.get("content")
                text = body if isinstance(body, str) else json.dumps(
                    body, ensure_ascii=False)
                # One faulted result is one fault: an overload message carries
                # both a status code and the word, and counting matches instead
                # of results doubled every number in the first draft.
                # Prefer the status code wherever it appears; the surrounding
                # sentence is leftmost in the message, so ordinary leftmost
                # matching would have labelled every fault with the prose.
                found = pattern.search(text)
                if found:
                    hits[found.group(1)] = hits.get(found.group(1), 0) + 1
                elif generic.search(text):
                    hits["api-error"] = hits.get("api-error", 0) + 1
    return {"seen": sum(hits.values()), "by_kind": hits}


def criterion_3(run: Path) -> dict:
    """Did every dispatch this run made end up answered in its own ledger?

    Both sides have to be counted, and the first draft counted one. Logging a
    dispatch with `experience-log --from-pending` **consumes** the stub — the
    script rewrites the pending file without it — so a fully reconciled run
    ends with an empty pending file, which the first draft reported as
    `staged: 0, unreconciled: 0`: exactly what a run that never dispatched
    anything reports. Two opposite states, one number, and it read as good news
    both times. That is the worst way for a check to be wrong, and it had
    already produced one wrong sentence about a batch before it was caught.

    So the ledger is counted too. `still_staged 0 / logged 2` is a run that did
    its bookkeeping, `0 / 0` is a run that had none to do, and `2 / 0` is the
    lapse this criterion exists to catch.
    """
    telemetry = run / "telemetry"
    pending = telemetry / "experience-pending.jsonl"
    ledger = telemetry / "experience.jsonl"

    answered, logged = set(), 0
    for line in log_lines(ledger):
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("dispatch_id"):
            answered.add(row["dispatch_id"])
            logged += 1

    staged: dict[str, str] = {}
    for line in log_lines(pending):
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("dispatch_id"):
            staged.setdefault(row["dispatch_id"], row.get("agent_type", "?"))

    open_ids = sorted(key for key in staged if key not in answered)
    return {"still_staged": len(staged), "logged": logged,
            "unreconciled": len(open_ids), "open": open_ids,
            "reconciled": not open_ids,
            "had_bookkeeping_to_do": bool(staged or logged)}


def grade(run: Path) -> dict:
    """The whole verdict for one run, recomputed from its retained artifacts.

    Exposed as a function so `summarise.py` can rebuild a batch table from the
    runs rather than from the `verdict.json` files sitting next to them. Those
    files are written once, by whichever version of this grader was current at
    the time, and the first draft of the summariser duly folded a stale verdict
    from before the criterion-1 gate into a fresh batch. A number a reader will
    cite is recomputed, not read back.
    """
    run = run.resolve()
    meta = json.loads((run / "meta.json").read_text(encoding="utf-8"))
    scenario = meta["id"]
    if scenario not in GRADERS:
        raise SystemExit(f"no grader for {scenario!r}")

    turns = by_turn(read_events(run / "events.jsonl"))
    outcome = GRADERS[scenario](run, meta, turns)
    alive = criterion_1(meta)
    faults = api_faults(turns)

    # Criterion 1 gates the verdict, not just the report. The document says all
    # four criteria must hold before a result may be cited, and the first draft
    # here computed criterion 1 and then ignored it: on 2026-08-12 an `r3` run
    # was killed at TURN_TIMEOUT while retrying five leaf dispatches that the
    # API had answered with 529, and it came out scored `incorrect` — a clean
    # false negative about a session that never got to finish a sentence. A run
    # that did not end alive is not evidence in either direction.
    reasons = []
    if not outcome["marker_present"]:
        reasons.append("marker absent")
    if not alive["ended_alive"]:
        reasons.append("did not end alive")
    verdict = "invalid" if reasons else (
        "correct" if outcome["correct"] else "incorrect")

    report = {
        "run": run.name,
        "scenario": scenario,
        "measures": meta.get("measures"),
        "marker": meta["marker"],
        "recovery_point": meta["recovery_point"],
        "expect": meta["expect"],
        "verdict": verdict,
        "invalid_because": reasons or None,
        "criterion_1": alive,
        "criterion_3": criterion_3(run),
        "provider_faults": faults,
        "outcome": outcome,
        "contract_matched_repo_source": meta.get("matches_repo_source"),
        "arm": (meta.get("arm") or {}).get("arm", "a"),
        "arm_state": meta.get("arm"),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = grade(args.run)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if report["verdict"] == "invalid":
        return 2
    return 0 if report["verdict"] == "correct" else 1


if __name__ == "__main__":
    sys.exit(main())
