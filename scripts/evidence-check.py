#!/usr/bin/env python3
"""Is the recorded evidence still attached to anything real? Reports; never fails.

Two instruments, one question. Both were built after a 2026-08-08 check found
that most of this repo's evidence citations had quietly stopped resolving.

1. **Citations.** Every backtick-wrapped hex string in tracked markdown, sorted
   into resolves / dead / foreign. Foreign means the line also carries a URL, so
   the citation is about another repository and is not expected to resolve here;
   those are correctly formed today because they are full-length and linked. The
   dead ones are all bare short SHAs, which is the finding: in a repo that
   rebases branches before merging, a bare short SHA is not a durable anchor. It
   names a history that the next rebase rewrites.

2. **Trap evidence age.** Each trap declares its measured surface in
   `surface.tsv`; result rows stamped `[surface <short>]` are compared against
   the current fingerprint. A row whose stamp no longer matches is not wrong, it
   is *undated* - it measured rules that have since changed, and saying so is the
   whole point. Rows with no stamp predate the mechanism and count as unverified.

Exit status is always 0. This is an attestation, not a gate: a stale row is a
fact to weigh, and the legitimate reasons for one (the rules improved) outnumber
the illegitimate ones by far. Making it fail-closed would only teach people to
stop stamping rows.

Usage:
    scripts/evidence-check.py [--json]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CITATION = re.compile(r"`([0-9a-f]{7,40})`")
STAMP = re.compile(r"\[surface ([0-9a-f]{8})\]")
URL = re.compile(r"https?://")


def tracked_markdown() -> list[Path]:
    listed = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "*.md"],
        capture_output=True, text=True, check=True).stdout.split()
    return [ROOT / name for name in listed]


def resolves(sha: str) -> bool:
    return subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--verify", "-q", f"{sha}^{{commit}}"],
        capture_output=True).returncode == 0


def audit_citations() -> dict[str, list[dict[str, object]]]:
    buckets: dict[str, list[dict[str, object]]] = {
        "resolves": [], "foreign": [], "dead": []}
    seen: dict[str, dict[str, object]] = {}
    for path in tracked_markdown():
        relative = path.relative_to(ROOT).as_posix()
        for line in path.read_text(encoding="utf-8").splitlines():
            for sha in CITATION.findall(line):
                if sha.isdigit():
                    continue
                record = seen.setdefault(
                    sha, {"sha": sha, "sites": [], "linked": False})
                if relative not in record["sites"]:
                    record["sites"].append(relative)
                record["linked"] = record["linked"] or bool(URL.search(line))
    for sha, record in sorted(seen.items()):
        if resolves(sha):
            buckets["resolves"].append(record)
        elif record["linked"]:
            buckets["foreign"].append(record)
        else:
            buckets["dead"].append(record)
    return buckets


def audit_traps() -> list[dict[str, object]]:
    # `trap-surface.py` is not an importable module name (the hyphen), and
    # renaming it would break the command line it documents, so load it by path.
    location = ROOT / "evals" / "scripts" / "trap-surface.py"
    spec = importlib.util.spec_from_file_location("trap_surface", location)
    if spec is None or spec.loader is None:  # pragma: no cover - path typo
        raise SystemExit(f"cannot load {location}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fingerprint = module.fingerprint
    short = module.SHORT

    rows = []
    for listing in sorted((ROOT / "evals" / "traps").glob("*/surface.tsv")):
        trap = listing.parent.name
        current = fingerprint(trap)[0][:short]
        readme = listing.parent / "README.md"
        stamps = STAMP.findall(readme.read_text(encoding="utf-8")) if readme.exists() else []
        table = [line for line in readme.read_text(encoding="utf-8").splitlines()
                 if line.startswith("| 2026-")] if readme.exists() else []
        rows.append({
            "trap": trap,
            "current": current,
            "result_rows": len(table),
            "stamped": len(stamps),
            "current_stamps": sum(1 for stamp in stamps if stamp == current),
            "stale_stamps": sum(1 for stamp in stamps if stamp != current),
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="machine-readable")
    args = parser.parse_args()

    citations = audit_citations()
    traps = audit_traps()

    if args.json:
        print(json.dumps({"citations": citations, "traps": traps}, indent=2))
        return 0

    total = sum(len(bucket) for bucket in citations.values())
    print(f"citations: {total} distinct, "
          f"{len(citations['resolves'])} resolve, "
          f"{len(citations['foreign'])} foreign (linked), "
          f"{len(citations['dead'])} dead")
    for record in citations["dead"]:
        print(f"  dead  {record['sha']}")
        for site in record["sites"]:
            print(f"          {site}")

    print()
    print("trap evidence:")
    for row in traps:
        unverified = row["result_rows"] - row["stamped"]
        print(f"  {row['trap']:<22} surface {row['current']}  "
              f"rows {row['result_rows']:>3}  "
              f"current {row['current_stamps']:>3}  "
              f"stale {row['stale_stamps']:>3}  "
              f"unverified {unverified:>3}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
