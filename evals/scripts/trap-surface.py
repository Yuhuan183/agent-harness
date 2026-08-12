#!/usr/bin/env python3
"""Content fingerprint for a trap's measured surface.

A trap result says "this is how the agent behaved under these rules". Naming the
rules by commit SHA does not survive this repo's workflow: on 2026-08-08 six of
the ten local SHA citations in the tree resolved to nothing, because branches are
rebased before merge and a rebase rewrites every SHA a note was written against.

A fingerprint over file *contents* has no such problem. It is computed from the
bytes that were measured, so it stays correct across rebases, moves and renames,
and it answers the question a reader actually has - "do the rules still say what
they said when this number was produced?" - which a SHA only answers indirectly.

Stamp a new result row with the short form:

    evals/scripts/trap-surface.py --trap s7-false-completion
    surface d4f1a0b9

then write `[surface d4f1a0b9]` into the row. `scripts/evidence-check.py` reads
those back and reports which rows are still attached to the shipping bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHORT = 8


def listing_for(name: str) -> Path:
    """Find `<name>/surface.tsv` anywhere one level under `evals/`.

    Traps are not the only thing that measures behaviour: `evals/replay/` runs
    multi-turn sessions and needs the same fingerprint for the same reason. One
    instrument covers both rather than two that can drift apart.
    """
    found = sorted(ROOT.glob(f"evals/*/{name}/surface.tsv"))
    if len(found) == 1:
        return found[0]
    if not found:
        direct = ROOT / "evals" / name / "surface.tsv"
        if direct.exists():
            return direct
    raise SystemExit(f"{name}: expected exactly one surface.tsv under evals/, "
                     f"found {len(found)}; a suite without a declared surface "
                     "cannot date its own evidence")


def surface_paths(trap: str) -> list[str]:
    listing = listing_for(trap)
    paths = []
    for raw in listing.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            paths.append(line)
    return sorted(paths)


def fingerprint(trap: str) -> tuple[str, list[dict[str, str]]]:
    members = []
    binding = hashlib.sha256()
    for path in surface_paths(trap):
        target = ROOT / path
        if not target.exists():
            raise SystemExit(f"{trap}: surface lists {path}, which is gone; "
                             "fix the surface before trusting any fingerprint")
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        binding.update(path.encode("utf-8"))
        binding.update(b"\0")
        binding.update(digest.encode("ascii"))
        binding.update(b"\n")
        members.append({"path": path, "sha256": digest})
    return binding.hexdigest(), members


def traps() -> list[str]:
    return sorted({entry.parent.name
                   for entry in ROOT.glob("evals/*/*/surface.tsv")}
                  | {entry.parent.name
                     for entry in ROOT.glob("evals/*/surface.tsv")})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trap", help="trap directory name; default is all")
    parser.add_argument("--json", action="store_true", help="machine-readable")
    args = parser.parse_args()

    selected = [args.trap] if args.trap else traps()
    report = {}
    for trap in selected:
        full, members = fingerprint(trap)
        report[trap] = {"surface": full, "short": full[:SHORT],
                        "members": members}

    if args.json:
        print(json.dumps(report, indent=2))
        return 0
    for trap, record in report.items():
        label = f"{trap}: " if len(report) > 1 else ""
        print(f"{label}surface {record['short']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
