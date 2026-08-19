#!/usr/bin/env python3
"""Sweep this repo's own Chinese prose for the terms it ships a table to correct.
Reports; never fails.

`readable-zh-tw` carries a 中國用語 replacement table and deploys it so the skill
can clean somebody else's copy. Nothing pointed it back here, and on 2026-08-19 a
review found 智能體 in the title of `docs/setup.md` - the exact term row 19 of
that table maps to 智慧. One term is a thin case for a gate; it is a sufficient
case for a report, which is the same call `docs/` got for size.

The term list is read from the shipped table rather than copied, so adding a row
there covers this sweep too and the two cannot disagree.

Deliberately not a gate. A word list cannot tell 用 from 提及: a document that
discusses the term 「智能」 is doing the right thing, and a checker that fails on
it would train people to phrase around the checker. Read the hits and decide.

Exclusions, each for a stated reason rather than to keep the output clean:
  - the table itself, which is the word list;
  - `harness-review`'s probes, where the terms are search patterns;
  - `evals/**`, whose fixtures carry deliberate defects as match data.

Usage:
    scripts/zh-tw-usage-report.py [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "main/.agents/skills/readable-zh-tw/references/taiwan-localization.md"
EXEMPT_PATHS = {
    ".agents/skills/harness-review/references/probes.md",
}
# The whole skill, not just the table: `protected-list.md` quotes 賦能 as an
# example of a term being *mentioned* rather than used, which is the same
# category as the word list itself.
EXEMPT_PREFIX = "main/.agents/skills/readable-zh-tw/"

# Calibration, and it changed the tool rather than the tree. The first run
# returned 60 hits of which 57 were 落地 - vocabulary this repo uses as a term of
# art in almost every research document, and which reads as ordinary Taiwan
# technical writing. An instrument that reports 57 false positives is the
# permanent alarm this repo keeps warning about, so the term is exempted here
# with the reason attached rather than quietly dropped from the table, which
# would change what the skill teaches about somebody else's marketing copy.
#
# This is not a place to park inconvenient hits. A term belongs here only when
# the repo's usage is a different sense or an established local convention, and
# the entry has to say which.
EXEMPT_TERMS = {
    "落地": "used throughout as 已落地 = shipped; ordinary Taiwan technical usage "
            "here, and the table's row targets marketing prose",
}
ROW = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$", re.MULTILINE)


def terms() -> dict[str, str]:
    """Left column to right column, split on the ／ the table uses for variants."""
    out: dict[str, str] = {}
    for prc, tw in ROW.findall(TABLE.read_text(encoding="utf-8")):
        if prc in ("中國用語", ":--") or prc.startswith(":-"):
            continue
        for one in prc.split("／"):
            one = one.strip()
            if one:
                out[one] = tw
    return out


def sweep() -> list[dict[str, object]]:
    listed = subprocess.run(["git", "ls-files", "*.md"], cwd=ROOT,
                            capture_output=True, text=True).stdout.split()
    table = terms()
    hits = []
    for name in listed:
        if (name in EXEMPT_PATHS or name.startswith("evals/")
                or name.startswith(EXEMPT_PREFIX)):
            continue
        text = (ROOT / name).read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), 1):
            for prc, tw in table.items():
                if prc in EXEMPT_TERMS:
                    continue
                if prc in line:
                    hits.append({"path": name, "line": line_number,
                                 "term": prc, "suggested": tw,
                                 "context": line.strip()[:100]})
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="machine-readable")
    args = parser.parse_args()
    hits = sweep()
    if args.json:
        print(json.dumps({"terms": len(terms()), "hits": hits},
                         ensure_ascii=False, indent=2))
        return 0
    print(f"{len(terms())} terms from {TABLE.relative_to(ROOT)}, "
          f"{len(EXEMPT_TERMS)} exempted here")
    for term, why in sorted(EXEMPT_TERMS.items()):
        print(f"  exempt: {term} - {why}")
    if not hits:
        print("no hits in tracked Chinese prose")
        return 0
    for hit in hits:
        print(f"  {hit['path']}:{hit['line']}  {hit['term']} -> {hit['suggested']}")
        print(f"      {hit['context']}")
    print(f"\n{len(hits)} hit(s). Read them: a document *about* a term is not a "
          "document using it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
