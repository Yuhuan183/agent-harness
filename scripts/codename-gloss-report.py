#!/usr/bin/env python3
"""Report internal codenames used without explanation. Reports; never fails.

`docs/README.md` rule 8 splits documents by reader, and one tier - 說明與研究 -
promises that the reader does not have to already know this repo's vocabulary.
That promise had no mechanism, and on 2026-08-20 the architecture overview broke
it in its own newest section: `s11`, `p1b` and `d1`/`d2` all appeared with
nothing saying what they are.

They are trap and replay scenario ids, so the inventory is derivable rather than
a list someone has to maintain: `evals/traps/*` and `evals/replay/runs/*` are
the two places those names come from.

What counts as explained is deliberately loose. The rule is "先具體，後命名",
and forcing every first use into a parenthetical would push the prose the other
way, so a first use passes when its own sentence carries any explanatory
apparatus - a parenthetical, an em-dash clause, or a colon. That admits a
sentence that merely looks explanatory. It is the wrong error to optimise away:
this is a reading aid, not a gate, and a scan that cries wolf gets muted.

The scanned set comes from rule 8's own table, so adding a document to that tier
extends this scan and nothing has to be updated here. Research journals are not
in it: they are written for whoever ran the batch.

Usage:
    scripts/codename-gloss-report.py [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TIER_ROW = re.compile(r"^\s*\|\s*說明與研究\s*\|(.+?)\|", re.MULTILINE)
LINK = re.compile(r"\]\(([^)]+\.md)\)")
APPARATUS = ("(", "（", "——", ":", "：")


def scanned_documents() -> list[str]:
    """The 說明與研究 row of `docs/README.md` rule 8 is the inventory."""
    row = TIER_ROW.search((ROOT / "docs/README.md").read_text(encoding="utf-8"))
    if row is None:
        raise SystemExit("docs/README.md: no 說明與研究 row in the reader table")
    return [f"docs/{target}" for target in LINK.findall(row.group(1))]


def codenames() -> list[str]:
    """Trap directories and replay run directories, longest first so that `s10`
    is matched before `s1` would be."""
    names = {path.name.split("-")[0]
             for path in (ROOT / "evals/traps").iterdir() if path.is_dir()}
    names |= {path.name.split("-")[0]
              for path in (ROOT / "evals/replay/runs").iterdir() if path.is_dir()}
    return sorted(names, key=lambda name: (-len(name), name))


def sentence_around(text: str, start: int, end: int) -> str:
    left = max(text.rfind(mark, 0, start) for mark in ("。", "\n", "|", ". "))
    right = min((pos for pos in
                 (text.find(mark, end) for mark in ("。", "\n", "|", ". "))
                 if pos != -1), default=len(text))
    return text[left + 1:right]


def measure() -> dict:
    names = codenames()
    token = re.compile(rf"(?<![\w-])({'|'.join(names)})(?![\w-])")
    version = re.compile(r"^\.\d")
    rows = []
    for relative in scanned_documents():
        path = ROOT / relative
        if not path.exists():
            rows.append({"path": relative, "codename": None,
                         "note": "listed in the reader table but missing"})
            continue
        text = path.read_text(encoding="utf-8")
        seen = set()
        for match in token.finditer(text):
            name = match.group(1)
            if name in seen or version.match(text[match.end():match.end() + 2]):
                continue
            seen.add(name)
            sentence = sentence_around(text, match.start(), match.end())
            if any(mark in sentence for mark in APPARATUS):
                continue
            rows.append({
                "path": relative,
                "line": text[:match.start()].count("\n") + 1,
                "codename": name,
                "sentence": " ".join(sentence.split())[:120],
            })
    return {"codenames": names, "scanned": scanned_documents(), "unglossed": rows}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="machine-readable")
    args = parser.parse_args()

    result = measure()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(f"{len(result['codenames'])} codenames from evals/traps and "
          f"evals/replay/runs, scanning {len(result['scanned'])} documents "
          "named by docs/README.md rule 8")
    for row in result["scanned"]:
        print(f"  {row}")
    print()
    for row in result["unglossed"]:
        if row["codename"] is None:
            print(f"  {row['path']}: {row['note']}")
            continue
        print(f"  {row['path']}:{row['line']}  {row['codename']}")
        print(f"      {row['sentence']}")
    total = len(result["unglossed"])
    print(f"\n{total} first use(s) with nothing explaining them. A reader of "
          "this tier should not have to open evals/ to find out what a name is.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
