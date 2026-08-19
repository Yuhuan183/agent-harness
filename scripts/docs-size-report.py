#!/usr/bin/env python3
"""Size report for the repo-only `docs/` tree. Reports; never fails.

The deployed surface is measured by `scripts/prompt-surface-census.py` and
ratcheted by word budgets, because a session pays for those bytes on every turn
or every dispatch. `docs/` is the other cost model: nothing under it is in
`scripts/deployment-manifest.tsv`, so it is paid only when a reader or an agent
opens a file, once, having asked for it. That does not make its size
uninteresting - it makes a commit-gating ceiling the wrong instrument.

So this is the instrument instead: run it when you want to know whether the tree
is sprawling, and decide with your eyes. The only mechanical check on this tree
is `DOC_SPRAWL_CEILING`, which catches a document that has stopped being one
document and nothing else.

The total alone is the wrong number to look at, and reading it as one number
produced a wrong finding on 2026-08-19: `docs/research/` is three quarters of
this tree, but almost none of it claims to be current. It is a lab journal that
keeps its refuted entries on purpose. What has to stay true - and therefore what
has to be re-read whenever the design moves - is the guidance tier. So the two
tiers are reported separately, taken from `docs/document-inventory.json` rather
than from a rule restated here.

`main/claude/tests/test_document_inventory.py` owns coverage and classification;
this script only reports what that envelope currently says.

Usage:
    scripts/docs-size-report.py [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "docs/document-inventory.json"


def word_count(text: str) -> int:
    """Same unit as the deployed budgets: one per CJK character, one per other
    non-space run. Kept identical so the two tiers stay comparable."""
    return len(re.findall(r"[一-鿿]|[^\s一-鿿]+", text))


def classify(relative: str, inventory: dict[str, list[str]]) -> str:
    """Guidance, evidence, or unclassified, per the inventory's own precedence:
    an exact path beats a glob, so `docs/research/README.md` stays guidance
    while its siblings are evidence."""
    guidance = inventory["reviewed_current_guidance"]
    evidence = inventory["evidence_not_current_guidance"]
    if relative in guidance:
        return "guidance"
    if relative in evidence:
        return "evidence"
    if any(PurePosixPath(relative).full_match(rule) for rule in evidence):
        return "evidence"
    if any(PurePosixPath(relative).full_match(rule) for rule in guidance):
        return "guidance"
    return "unclassified"


def measure() -> list[dict[str, object]]:
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    rows = []
    for path in sorted((ROOT / "docs").rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(ROOT).as_posix()
        rows.append({
            "path": relative,
            "tier": classify(relative, inventory),
            "words": word_count(text),
            "bytes": len(text.encode("utf-8")),
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="machine-readable")
    args = parser.parse_args()

    rows = measure()
    if args.json:
        print(json.dumps({"unit": "word_count", "docs": rows}, indent=2))
        return 0

    width = max((len(row["path"]) for row in rows), default=0)
    total = sum(row["words"] for row in rows)
    for tier in ("guidance", "evidence", "unclassified"):
        group = [row for row in rows if row["tier"] == tier]
        if not group:
            continue
        subtotal = sum(row["words"] for row in group)
        print(f"[{tier}]  {subtotal}w  {100 * subtotal / total:.0f}% of the tree"
              f"  across {len(group)} documents")
        for row in sorted(group, key=lambda row: -row["words"]):
            print(f"  {row['path']:<{width}}  {row['words']:>6}w"
                  f"  {row['bytes']:>7}B")
        print()
    print(f"{total}w across {len(rows)} documents. Only the guidance tier has "
          f"to stay true; the evidence tier records what was checked, "
          f"including what was later overturned.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
