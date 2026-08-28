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
import re
from pathlib import Path

# A leaf is told its workdir as an absolute path, so it quotes one back in
# almost every report. The part that carries meaning is the location inside the
# tree; the username and machine layout are not evidence and this repository is
# published. Applied at the moment of writing, so no retained artefact ever
# holds one and no reviewer has to notice - which is the step that failed on
# 2026-08-28, when 600 occurrences across two usernames had accumulated and the
# reviewer looked at fresh ones and called them pre-existing convention.
_REPO_ABS = re.compile(r"/Users/[A-Za-z0-9._-]+/WorkSpace/agent-harness")
_HOME_ABS = re.compile(r"/Users/[A-Za-z0-9._-]+")


def redact(text: str) -> str:
    """Replace machine-local absolute paths with stable placeholders.

    Longest first: the repository root is more specific than the home root, and
    folding the home first would leave `<HOME>/WorkSpace/agent-harness` behind.
    """
    return _HOME_ABS.sub("<HOME>", _REPO_ABS.sub("<REPO>", text))


def keep(target: Path | None, report: str, verdict: dict) -> None:
    """Copy the graded report and its verdict into `target`.

    A no-op when `target` is None, so adding the flag breaks no existing
    invocation. The report is written as graded except that machine-local
    absolute paths are redacted - stated here rather than claimed byte-for-byte,
    because a claim of exactness that is not exact is worse than the redaction.
    Nothing a rescore reads is affected: the gate lines, the reasoning and the
    file names all survive, only the home prefix changes.
    """
    if target is None:
        return
    target.mkdir(parents=True, exist_ok=True)
    (target / "report.md").write_text(redact(report), encoding="utf-8")
    # The verdict quotes the report's own text back in its findings, so it
    # carries the same paths and needs the same treatment.
    (target / "verdict.json").write_text(
        redact(json.dumps(verdict, indent=2)) + "\n", encoding="utf-8")


def add_argument(parser) -> None:
    """Register `--keep` with one wording, so four graders cannot describe it
    four ways."""
    parser.add_argument(
        "--keep", type=Path, default=None,
        help="directory to copy the graded report and this verdict into, so a "
             "later question can be asked of the same bytes")
