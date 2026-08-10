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

Usage:
    scripts/docs-size-report.py [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def word_count(text: str) -> int:
    """Same unit as the deployed budgets: one per CJK character, one per other
    non-space run. Kept identical so the two tiers stay comparable."""
    return len(re.findall(r"[一-鿿]|[^\s一-鿿]+", text))


def measure() -> list[dict[str, object]]:
    rows = []
    for path in sorted((ROOT / "docs").rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        rows.append({
            "path": path.relative_to(ROOT).as_posix(),
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
    for row in sorted(rows, key=lambda row: -row["words"]):
        print(f"{row['path']:<{width}}  {row['words']:>6}w  {row['bytes']:>7}B")
    total = sum(row["words"] for row in rows)
    print(f"{'':<{width}}  {total:>6}w  across {len(rows)} documents")
    return 0


if __name__ == "__main__":
    sys.exit(main())
