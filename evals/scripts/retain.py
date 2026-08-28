#!/usr/bin/env python3
"""Keep the bytes a grader judged, beside the verdict it reached.

Why this exists. Every trap grader that takes `--report` read the file, judged
it, and kept nothing, so a run survived as one row in a results table. That is
enough to re-read a conclusion and not enough to ask a *new* question of an old
run. The bill arrived on 2026-08-28: a continuous scale for the `INTENT:` line
landed with a condition to rescore the seeds already graded, and not one of the
37 rows could be rescored, because no report had been kept.

Both halves or neither. Bytes with no verdict cannot be checked against what
was concluded at the time; a verdict with no bytes is the situation this
replaces. Writing them together is the point.

Deliberately repo-only. It sits under `evals/scripts/` rather than
`main/.agents/scripts/` because nothing in a deployed session grades a trap;
`gate_lines.py` lives on the other side of that line because production QC
shares its regexes.
"""
from __future__ import annotations

import json
from pathlib import Path


def keep(target: Path | None, report: str, verdict: dict) -> None:
    """Copy the graded report and its verdict into `target`.

    A no-op when `target` is None, so adding the flag breaks no existing
    invocation. The report is written byte-for-byte as graded rather than
    re-serialised: a rescore compares against what the grader actually saw, and
    a normalising round-trip would quietly change the thing being preserved.
    """
    if target is None:
        return
    target.mkdir(parents=True, exist_ok=True)
    (target / "report.md").write_text(report, encoding="utf-8")
    (target / "verdict.json").write_text(
        json.dumps(verdict, indent=2) + "\n", encoding="utf-8")


def add_argument(parser) -> None:
    """Register `--keep` with one wording, so four graders cannot describe it
    four ways."""
    parser.add_argument(
        "--keep", type=Path, default=None,
        help="directory to copy the graded report and this verdict into, so a "
             "later question can be asked of the same bytes")
