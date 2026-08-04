#!/usr/bin/env python3
"""Report how a diff moved the logical operators inside prompt-surface files.

Evidence, not a gate. It always exits 0 and never blocks anything, because the
legal changes to a connective vastly outnumber the illegal ones: a fail-closed
version would be mostly false positives, and a check that is mostly false
positives gets bypassed or allowlisted until it is worse than nothing. A human
reads the table; this script only makes forgetting to look impossible.

The gap it covers: the acceptance suite asserts that phrases are present. A
compression pass that turns "A or B" into "A and B", or drops an "unless",
leaves every asserted phrase intact and still changes what the contract means.
Upstream Pilotfish v1.3.7 passed 255 phrase assertions verbatim and shipped
twelve semantic defects, one of which made a disposition unreachable. This
repository has its own instance: a resident clause that lost its subject to a
540/540 word budget and then read as though the sandbox substitutes programs.

Operators tracked are the ones in docs/contract-slimming.md, plus `not`,
`every`, and `at least` — the specified list carries `never` and `each` and
`at most` but not their partners, and a pass that swaps one for the other is
exactly the class this table exists to surface.

Usage:
    scripts/contract-operator-delta.py                 # HEAD vs working tree
    scripts/contract-operator-delta.py --staged        # HEAD vs the index
    scripts/contract-operator-delta.py --range A..B    # between two commits
    scripts/contract-operator-delta.py --json
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Every file a session actually loads as instructions: both resident contracts,
# every leaf role on both providers, and every skill body. Research notes and
# tests are out of scope — they are read by people, not obeyed by models.
SURFACE_GLOBS = (
    "main/claude/CLAUDE.contract.md",
    "main/codex/AGENTS.contract.md",
    "main/codex/ANALYSIS.md",
    "main/codex/DEPLOY.md",
    "main/claude/agents/*.md",
    "main/codex/agents/*.toml",
    "main/claude/skills/*/SKILL.md",
    "main/claude/skills/*/references/*.md",
    "main/codex/skills/*/SKILL.md",
    "main/codex/skills/*/references/*.md",
    "main/.agents/skills/*/SKILL.md",
    "main/.agents/skills/*/references/*.md",
)

OPERATORS = (
    "and",
    "or",
    "not",
    "never",
    "only",
    "every",
    "each",
    "unless",
    "before",
    "after",
    "at most",
    "at least",
)


def word_count(text: str) -> int:
    """The repository's CJK-aware resident-attention budget unit."""
    return len(re.findall(r"[一-鿿]|[^\s一-鿿]+", text))


def operator_counts(text: str) -> dict[str, int]:
    lowered = text.lower()
    counts = {}
    for operator in OPERATORS:
        pattern = r"\b" + r"\s+".join(re.escape(part) for part in operator.split()) + r"\b"
        counts[operator] = len(re.findall(pattern, lowered))
    return counts


def git(*args: str) -> str:
    result = subprocess.run(
        ("git", *args), cwd=ROOT, capture_output=True, text=True, check=False)
    return result.stdout if result.returncode == 0 else ""


def in_surface(path: str) -> bool:
    return any(fnmatch.fnmatch(path, glob) for glob in SURFACE_GLOBS)


def changed_paths(base: str, target: str | None, staged: bool) -> list[str]:
    if target is not None:
        raw = git("diff", "--name-only", f"{base}..{target}")
    elif staged:
        raw = git("diff", "--name-only", "--cached", base)
    else:
        raw = git("diff", "--name-only", base)
    return sorted(p for p in raw.splitlines() if p and in_surface(p))


def blob(ref: str | None, path: str) -> str:
    if ref is None:
        candidate = ROOT / path
        return candidate.read_text(encoding="utf-8") if candidate.exists() else ""
    return git("show", f"{ref}:{path}")


def compare(base: str, target: str | None, staged: bool) -> list[dict]:
    reports = []
    for path in changed_paths(base, target, staged):
        if staged and target is None:
            after_text = git("show", f":{path}")
        else:
            after_text = blob(target, path)
        before = operator_counts(blob(base, path))
        after = operator_counts(after_text)
        rows = [
            {"operator": op, "before": before[op], "after": after[op],
             "delta": after[op] - before[op]}
            for op in OPERATORS
        ]
        reports.append({
            "path": path,
            "words_before": word_count(blob(base, path)),
            "words_after": word_count(after_text),
            "operators": rows,
            "moved": sum(abs(row["delta"]) for row in rows),
        })
    return reports


def render(reports: list[dict], label: str) -> str:
    lines = [f"contract operator delta: {label}"]
    if not reports:
        lines.append("  no prompt-surface file changed")
        return "\n".join(lines)
    for report in reports:
        words = report["words_after"] - report["words_before"]
        lines.append("")
        lines.append(f"  {report['path']}  ({words:+d} words)")
        moved = [row for row in report["operators"] if row["delta"]]
        if not moved:
            lines.append("    no tracked operator moved")
            continue
        for row in moved:
            lines.append(
                f"    {row['operator']:<9} {row['before']:>4} -> {row['after']:>4}"
                f"  ({row['delta']:+d})")
    total = sum(report["moved"] for report in reports)
    lines.append("")
    lines.append(f"  {total} operator occurrence(s) moved across "
                 f"{len(reports)} file(s) — read them, this is not a gate")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", default="HEAD", help="ref to compare from")
    parser.add_argument("--range", dest="range_spec", default=None,
                        help="A..B; overrides --base and --staged")
    parser.add_argument("--staged", action="store_true",
                        help="compare the index instead of the working tree")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    if args.range_spec:
        base, _, target = args.range_spec.partition("..")
        if not target:
            parser.error("--range needs the A..B form")
        label = args.range_spec
    else:
        base, target = args.base, None
        label = f"{base} -> {'index' if args.staged else 'working tree'}"

    reports = compare(base, target, args.staged)
    if args.json:
        print(json.dumps({"label": label, "files": reports}, indent=2, sort_keys=True))
    else:
        print(render(reports, label))
    return 0


if __name__ == "__main__":
    sys.exit(main())
