#!/usr/bin/env python3
"""Do the CLI's memories still point at things that exist? Reports; never fails.

Why this exists. `docs/architecture/context-engineering.md` lists three places
state outlives a window, and the memory directory is the only one with no
freshness check at all. Git is checked by the suite; the ledger is checked by
`weekly-integrity`. A memory entry records what was true when it was written and
then nothing revisits it - so when a file it names is renamed or deleted, the
entry keeps being recalled and keeps sounding authoritative.

That failure is quiet by construction: a memory arrives as background context in
a `<system-reminder>`, not as something anyone opens. The entry that says "edit
`main/claude/CLAUDE.contract.md`, not the deployed copy" is worth exactly as much
as that path being real.

What it checks:

- every repo-relative path a memory names still resolves in this checkout;
- every `[[wikilink]]` resolves to a memory that exists;
- the `MEMORY.md` index and the memory files agree in both directions.

Deliberately conservative about what counts as a path: only tokens containing a
`/`. A bare filename in prose (`openai_yaml.md`) is usually a reference to
something upstream or long gone, and flagging those would make this report noise
- and a report people learn to ignore is worse than no report.

Evidence class: machine-local. The memory directory belongs to the user and this
only reads it.

Usage:
    scripts/memory-freshness-report.py [--json]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEMORY = Path(os.path.expanduser(
    f"~/.claude/projects/{str(ROOT).replace('/', '-')}/memory"))

# a repo path in prose is nearly always inside backticks or a markdown link
PATHISH = re.compile(r"`([^`\n]+)`|\]\(([^)\s#]+)")
WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")
# MULTILINE, because without it `^` anchors to the start of the whole
# file and only the first index row is ever seen - which made the first
# run of this report claim two indexed memories were missing (2026-08-21).
INDEX_ROW = re.compile(r"^- \[[^\]]+\]\(([^)]+)\)", re.MULTILINE)


def repo_paths(text: str) -> list[str]:
    found = []
    for backticked, linked in PATHISH.findall(text):
        token = (backticked or linked).strip()
        if "/" not in token or token.startswith(("~", "http", "#")):
            continue
        # strip a trailing sentence particle or punctuation
        token = token.rstrip(".,;:)")
        found.append(token)
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--memory-dir", default=None,
                        help="read this directory instead of the CLI's "
                             "(the suite uses it; there is no other reason)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    memory = Path(args.memory_dir) if args.memory_dir else MEMORY
    if not memory.is_dir():
        print(f"no memory directory at {memory}")
        return 0

    entries = sorted(p for p in memory.glob("*.md") if p.name != "MEMORY.md")
    index = memory / "MEMORY.md"
    indexed = (set(INDEX_ROW.findall(index.read_text(encoding="utf-8")))
               if index.exists() else set())

    missing_paths: list[tuple[str, str]] = []
    dangling_links: list[tuple[str, str]] = []
    for entry in entries:
        text = entry.read_text(encoding="utf-8")
        for token in repo_paths(text):
            if not (ROOT / token).exists():
                missing_paths.append((entry.name, token))
        for link in WIKILINK.findall(text):
            if not (memory / f"{link}.md").exists():
                dangling_links.append((entry.name, link))

    names = {e.name for e in entries}
    unindexed = sorted(names - indexed)
    orphan_rows = sorted(indexed - names)

    report = {
        "memory": str(memory),
        "entries": len(entries),
        "missing_paths": [{"entry": e, "path": p} for e, p in missing_paths],
        "dangling_links": [{"entry": e, "link": l} for e, l in dangling_links],
        "not_in_index": unindexed,
        "index_rows_without_a_file": orphan_rows,
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    print(f"{len(entries)} memor(ies) under {memory}")
    clean = True
    if missing_paths:
        clean = False
        print("\n指到不存在的 repo 路徑:")
        for entry, path in missing_paths:
            print(f"  {entry}: {path}")
    if dangling_links:
        clean = False
        print("\n[[連結]] 指向不存在的記憶:")
        for entry, link in dangling_links:
            print(f"  {entry}: [[{link}]]")
    if unindexed:
        clean = False
        print("\n有檔案但 MEMORY.md 沒有列:")
        for name in unindexed:
            print(f"  {name}")
    if orphan_rows:
        clean = False
        print("\nMEMORY.md 列了但檔案不在:")
        for name in orphan_rows:
            print(f"  {name}")
    if clean:
        print("每一條指涉都還解得開.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
