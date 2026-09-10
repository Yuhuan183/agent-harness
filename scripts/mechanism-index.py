#!/usr/bin/env python3
# Read: when a research conclusion is retracted or overturned, before deciding what else moves
"""Which mechanisms does each research document name, and vice versa? Reports; never fails.

Why this exists. The evidence tier and the mechanism tier point one way only.
A script's docstring says which document it serves, but no document lists what
it produced, so when a conclusion is retracted there is no mechanical way to
ask what was built on it. That happened twice on 2026-09-08 alone: a sample
size corrected from 67 to 37, and a decision rule for M1 retracted outright.
Both times the question "what else rests on this" was answered by memory.

What it does NOT claim. Naming is not depending. A document that mentions
`baton-dispatch` in passing is not evidence that anything was built on it, and
a mechanism whose reasoning lives in a dated incident rather than a document
will not appear against that document at all - which the 2026-09-08 M4 pass
measured directly: ten of eleven scripts thought to have no recorded reason
turned out to cite sibling scripts and incidents instead of `docs/` paths.

So this produces a **starting set to check**, not an answer. Its value is that
the set is derived rather than remembered, and that it can only be too large,
never too small for the documents it covers.

Usage:
    scripts/mechanism-index.py                 # mechanisms per document
    scripts/mechanism-index.py --by-mechanism  # documents per mechanism
    scripts/mechanism-index.py --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Where conclusions live. The journals are included on purpose: a conclusion
# that exists only in a journal is exactly the orphan this cannot otherwise see.
CORPUS = ("docs/research", "docs/plans")


def mechanisms() -> dict[str, str]:
    """Every mechanism this repo ships, by name, derived rather than listed."""
    found: dict[str, str] = {}
    for path in sorted((ROOT / "main/claude/hooks").glob("*.py")):
        found[path.stem] = "hook"
    if (ROOT / "main/claude/githooks/pre-commit").exists():
        found["githooks/pre-commit"] = "hook"
    for tree in ("main/claude/skills", "main/codex/skills", "main/.agents/skills"):
        for path in sorted((ROOT / tree).iterdir()):
            if path.is_dir():
                found.setdefault(path.name, "skill")
    for path in sorted((ROOT / "scripts").iterdir()):
        if path.suffix in (".py", ".sh") and path.stem != Path(__file__).stem:
            found[path.stem] = "script"
    for path in sorted((ROOT / "main/claude/agents").glob("*.md")):
        found.setdefault(path.stem, "role")
    return found


def documents() -> list[Path]:
    out: list[Path] = []
    for folder in CORPUS:
        out.extend(sorted((ROOT / folder).glob("*.md")))
    return out


def build() -> dict:
    names = mechanisms()
    # Each name is tested against the text on its own, so overlapping names
    # like `denial_log` and `denial-report` both resolve and ordering is
    # irrelevant. An earlier version sorted by length and carried a comment
    # explaining why that mattered; mutation showed removing the sort changed
    # nothing, so the comment was defending a line that did no work.
    by_doc: dict[str, list[str]] = {}
    for path in documents():
        text = path.read_text(encoding="utf-8", errors="replace")
        hits = [name for name in names if name in text]
        if hits:
            by_doc[str(path.relative_to(ROOT))] = sorted(hits)
    by_mech: dict[str, list[str]] = {}
    for doc, hits in by_doc.items():
        for name in hits:
            by_mech.setdefault(name, []).append(doc)
    return {
        "mechanisms": names,
        "by_document": by_doc,
        "by_mechanism": {k: sorted(v) for k, v in sorted(by_mech.items())},
        "unnamed": sorted(set(names) - set(by_mech)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--by-mechanism", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    index = build()
    if args.json:
        json.dump(index, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
        print()
        return 0

    if args.by_mechanism:
        print("mechanism -> the documents that name it\n")
        for name, docs in index["by_mechanism"].items():
            kind = index["mechanisms"][name]
            print(f"  {name:28} {kind:7} {len(docs):>3}  "
                  f"{', '.join(Path(d).name for d in docs[:3])}"
                  f"{' …' if len(docs) > 3 else ''}")
    else:
        print("document -> the mechanisms it names\n")
        for doc, hits in sorted(index["by_document"].items()):
            print(f"  {Path(doc).name:42} {len(hits):>3}  "
                  f"{', '.join(hits[:4])}{' …' if len(hits) > 4 else ''}")

    unnamed = index["unnamed"]
    print(f"\n{len(index['mechanisms'])} mechanism(s); {len(unnamed)} named by no "
          f"document in {', '.join(CORPUS)}")
    # Where else they are named, so the line above is not read as "orphan".
    # The evidence tier is what gets retracted; the guidance tier is not, and a
    # mechanism documented only there is described, just not by a conclusion.
    for name in unnamed:
        elsewhere = [str(p.relative_to(ROOT)) for p in sorted(ROOT.glob("docs/**/*.md"))
                     if not str(p.relative_to(ROOT)).startswith(tuple(CORPUS))
                     and name in p.read_text(encoding="utf-8", errors="replace")]
        where = ", ".join(Path(p).name for p in elsewhere[:3]) or "nowhere in docs/"
        print(f"  {name:28} named instead in: {where}")
    print("\nNaming is not depending: this is a set to check, not an answer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
