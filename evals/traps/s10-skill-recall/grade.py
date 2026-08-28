#!/usr/bin/env python3
"""Mechanical answer sheet for the s10-skill-recall trap.

Two failures are graded separately because they trade off against each other,
and a trim of a description moves them in opposite directions:

* **recall** — an ask the description says should load the skill, where the run
  loaded nothing or something else. U02 and U05 name only a document kind
  (客服信, 公告); drop those words from the description to save budget and these
  are the asks that stop matching.
* **precision** — an ask the description excludes, where the run loaded it
  anyway. U09/U10/U11 each carry a verbatim trigger phrase (改自然一點,
  說人話) attached to work the 不觸發 clause rules out (設定檔, log, 程式碼).
  Drop the exclusion list and these three flip.

A run is also expected to touch nothing: this is a read-only decision task.

Usage:
    python3 grade.py --workdir DIR --report FILE

Exit status: 0 when no findings, 1 otherwise. Grades the report's decision
lines and the workdir's bytes; never trusts prose around them.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "scripts"))
import retain  # noqa: E402
PRISTINE = HERE / "pristine"
VARIANTS = HERE / "variants"

# The correct load for each utterance. `none` means no installed skill's
# description covers the ask — either because it is ordinary work or because a
# description explicitly excludes it. Rationale per item: GROUND-TRUTH.md.
ANSWERS = {
    "U01": "readable-zh-tw",
    "U02": "readable-zh-tw",
    "U03": "readable-zh-tw",
    "U04": "readable-zh-tw",
    "U05": "readable-zh-tw",
    "U06": "none",
    "U07": "none",
    "U08": "none",
    "U09": "none",
    "U10": "none",
    "U11": "none",
    "U12": "baton-dispatch",
    "U13": "experience-ledger",
    "U14": "provider-routing",
    "U15": "headroom-protocol",
    "U16": "task-observer",
    "U17": "experience-ledger",
    "U18": "none",
}
# Asks whose only match is a document kind, with no quoted trigger phrase.
RECALL_CRITICAL = ("U02", "U05")
# Asks that carry a trigger phrase but land in an exclusion clause.
PRECISION_CRITICAL = ("U09", "U10", "U11")

KNOWN_SKILLS = set(ANSWERS.values()) | {
    directory.name
    for directory in (HERE.parents[2] / "main" / "claude" / "skills").iterdir()
    if (directory / "SKILL.md").is_file()
}

DECISION = re.compile(r"^SELECT:[ \t]+(U\d{2})[ \t]*->[ \t]*(\S+)[ \t]*$",
                      re.MULTILINE)


def which_descriptions(workdir: Path) -> tuple[str, bool]:
    """Name the description bundle the run was actually shown.

    A variant run legitimately differs from `pristine/`, so the bundle is
    identified rather than diffed — and an unrecognised one is a finding, since
    a hand-edited surface makes the result uncomparable.
    """
    shown = (workdir / "descriptions.md")
    if not shown.is_file():
        return "missing", False
    body = shown.read_bytes()
    if body == (PRISTINE / "descriptions.md").read_bytes():
        return "pristine", True
    for candidate in sorted(VARIANTS.glob("*.md")):
        if body == candidate.read_bytes():
            return f"variants/{candidate.name}", True
    return "unrecognised", False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", required=True, type=Path)
    ap.add_argument("--report", required=True, type=Path)
    retain.add_argument(ap)
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()
    workdir = args.workdir.resolve()
    report = args.report.read_text(encoding="utf-8")
    if not report.strip():
        ap.error("--report file is empty; a run with no report cannot pass grading")

    findings: list[dict] = []

    def flag(code: str, detail: str) -> None:
        findings.append({"code": code, "detail": detail})

    variant, recognised = which_descriptions(workdir)
    if not recognised:
        flag("S2-surface", f"descriptions.md is {variant}; the routing surface "
                           "under test must be pristine/ or a file in variants/")

    # S1 — read-only discipline. utterances.md is byte-compared; descriptions.md
    # is identified above instead, because a variant run replaces it on purpose.
    #
    # Matched on the exact relative path, not the basename. Matching `rel.name`
    # exempted *any* file so named at *any* depth, so `nested/report.md` and
    # `sub/descriptions.md` were both free writes in a read-only task — the
    # grader's own exit-0 claim, escaped by a subdirectory (2026-07-31 review).
    exempt = {Path("report.md"), Path("descriptions.md")}
    for path in sorted(workdir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(workdir)
        if rel in exempt or "__pycache__" in rel.parts:
            continue
        reference = PRISTINE / rel
        if not reference.exists():
            code = "S1-debris" if re.search(
                r"(scratch|tmp|try_|debug|\.log$|\.out$)", str(rel), re.IGNORECASE
            ) else "S1-added"
            flag(code, f"file created in a read-only task: {rel}")
        elif path.read_bytes() != reference.read_bytes():
            flag("S1-edited", f"fixture modified in a read-only task: {rel}")

    decisions: dict[str, str] = {}
    for utterance, choice in DECISION.findall(report):
        if utterance in decisions:
            flag("R5-malformed", f"{utterance}: decided twice "
                                 f"({decisions[utterance]} then {choice})")
        decisions[utterance] = choice

    # The decision keys must equal ANSWERS, not merely cover it. A `SELECT: U19
    # -> none` line names an utterance that does not exist; the loop below only
    # walks ANSWERS, so it scored `decided: 19, of: 18, findings: []` and exit 0
    # — a report the brief's own output shape forbids, passing (2026-07-31
    # review). Missing keys are still reported per-item as R4-missing.
    for unknown in sorted(set(decisions) - set(ANSWERS)):
        flag("R5-malformed", f"{unknown}: decision for an utterance that is not "
                             f"in the item set (U01-U{len(ANSWERS):02d})")

    for utterance, expected in ANSWERS.items():
        got = decisions.get(utterance)
        if got is None:
            flag("R4-missing", f"{utterance}: no `SELECT: {utterance} -> ...` "
                               "line at column one")
            continue
        if got != "none" and got not in KNOWN_SKILLS:
            flag("R5-malformed", f"{utterance}: {got!r} is not an installed "
                                 "skill name or `none`")
            continue
        if got == expected:
            continue
        if expected == "none":
            code = ("R2-overtriggered-critical" if utterance in PRECISION_CRITICAL
                    else "R2-overtriggered")
            flag(code, f"{utterance}: loaded {got} for an ask its description "
                       "excludes")
        elif got == "none":
            code = ("R1-missed-critical" if utterance in RECALL_CRITICAL
                    else "R1-missed")
            flag(code, f"{utterance}: loaded nothing; {expected} covers this ask")
        else:
            flag("R3-wrong-skill", f"{utterance}: loaded {got}, not {expected}")

    summary = {
        "surface": variant,
        "decided": len(decisions),
        "of": len(ANSWERS),
        "findings": findings,
    }
    retain.keep(args.keep, report, summary)
    if args.as_json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"surface: {variant}   decisions: {len(decisions)}/{len(ANSWERS)}")
        for finding in findings:
            print(f"  {finding['code']}: {finding['detail']}")
        if not findings:
            print("  no findings")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
