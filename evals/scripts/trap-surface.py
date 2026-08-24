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
import subprocess
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


class SurfaceIncomplete(Exception):
    """A listed path is absent at the revision being fingerprinted.

    Fatal for the working tree - a surface that lists a file which is gone
    cannot date anything. Not fatal when walking history, where a revision
    predating a listed file simply cannot produce a fingerprint, and the caller
    moves on to the next one.
    """


# Walking history re-reads mostly-identical trees, so the expensive part is
# fetched once per blob rather than once per (commit, path): a listing of 51
# paths across 60 commits is ~3000 lookups but only a few hundred distinct
# blobs. Keyed by object id, which is what "the same bytes" means to git.
_TREE: dict[str, dict[str, str]] = {}
_BLOB_DIGEST: dict[str, str] = {}


def _tree(at: str) -> dict[str, str]:
    if at not in _TREE:
        listed = subprocess.run(
            ["git", "-C", str(ROOT), "ls-tree", "-r", "--format=%(objectname) %(path)", at],
            capture_output=True, text=True)
        _TREE[at] = dict(
            reversed(line.split(" ", 1)) for line in listed.stdout.splitlines() if " " in line)
    return _TREE[at]


def digest_at(path: str, at: str | None) -> str:
    """sha256 of `path`'s bytes in the working tree, or at a git revision."""
    if at is None:
        return hashlib.sha256(read_at(path, None)).hexdigest()
    oid = _tree(at).get(path)
    if oid is None:
        raise SurfaceIncomplete(path)
    if oid not in _BLOB_DIGEST:
        blob = subprocess.run(["git", "-C", str(ROOT), "cat-file", "blob", oid],
                              capture_output=True)
        if blob.returncode != 0:
            raise SurfaceIncomplete(path)
        _BLOB_DIGEST[oid] = hashlib.sha256(blob.stdout).hexdigest()
    return _BLOB_DIGEST[oid]


def read_at(path: str, at: str | None) -> bytes:
    """Bytes of `path` in the working tree, or at a git revision.

    A historical fingerprint has to be composed exactly the way a live one is,
    or the two answer different questions while looking comparable. So the
    composition below stays single and the source is what varies here.
    """
    if at is None:
        target = ROOT / path
        if not target.exists():
            raise SurfaceIncomplete(path)
        return target.read_bytes()
    shown = subprocess.run(["git", "-C", str(ROOT), "show", f"{at}:{path}"],
                           capture_output=True)
    if shown.returncode != 0:
        raise SurfaceIncomplete(path)
    return shown.stdout


def surface_paths(trap: str, at: str | None = None) -> list[str]:
    listing = listing_for(trap)
    # The listing itself is versioned: a fingerprint from before a path was
    # added was composed over the shorter list, so read the list from the same
    # revision as the files.
    rel = listing.relative_to(ROOT).as_posix()
    raw_text = read_at(rel, at).decode("utf-8")
    paths = []
    for raw in raw_text.splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            paths.append(line)
    return sorted(paths)


def fingerprint(trap: str, at: str | None = None) -> tuple[str, list[dict[str, str]]]:
    members = []
    binding = hashlib.sha256()
    for path in surface_paths(trap, at):
        digest = digest_at(path, at)
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
        try:
            full, members = fingerprint(trap)
        except SurfaceIncomplete as gone:
            raise SystemExit(
                f"{trap}: surface lists {gone}, which is gone; fix the surface "
                "before trusting any fingerprint")
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
