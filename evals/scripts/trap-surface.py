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

Stamp a new result row with the printed form:

    evals/scripts/trap-surface.py --trap s7-false-completion
    [surface d4f1a0b9 briefs:be69704d machinery:0dd7b6f3 roles:cd2c98a7 ...]

pasted verbatim into the row. A listing that declares groups puts each group's
digest in the stamp, so a later reader can see which half moved without
resolving the stamp back through git history - which stops working the day the
history is rewritten. An ungrouped listing keeps the short `[surface d4f1a0b9]`
form. `scripts/evidence-check.py` reads stamps back and reports which rows are
still attached to the shipping bytes; a retired row's stamp becomes
`[surface d4f1a0b9 archived]`, which stays counted as stamped but stops being
reported stale.
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
    """path -> object id at a revision.

    `--format` on ls-tree needs git 2.36. An older git prints a usage error and
    exits non-zero, and reading stdout regardless would hand back an empty map -
    at which point every path looks absent, every stamp looks unresolvable, and
    the report says something about this repository that is really about the
    tool. So the exit status is checked and the failure is loud.
    """
    if at not in _TREE:
        listed = subprocess.run(
            ["git", "-C", str(ROOT), "ls-tree", "-r", "--format=%(objectname) %(path)", at],
            capture_output=True, text=True)
        if listed.returncode != 0:
            raise RuntimeError(
                f"git ls-tree failed for {at}: {listed.stderr.strip()}; "
                "`--format` needs git 2.36 or newer")
        # split(" ", 1) keeps paths containing spaces intact: the object id
        # never has one, so the first space is always the separator.
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


DEFAULT_GROUP = "surface"


def surface_groups(trap: str, at: str | None = None) -> dict[str, list[str]]:
    """group -> paths, from a listing that may or may not declare groups.

    A bracketed line opens a group and every path after it belongs to that
    group until the next one; paths before any header fall in `surface`, which
    is also where an ungrouped listing puts everything.

    Groups exist because "the fingerprint moved" stopped being informative. The
    replay surface covers ten skill bodies - one scenario is decided by eight
    resident descriptions competing, so recording only the two under test would
    leave their competitors unfingerprinted - and the accepted cost was that a
    skill edit stales every row. Accepted, and then paid: 13 stamps, one
    resolving. Reading the same listing in two halves lets a report say the
    tested bytes held while the competing bytes moved, which is the distinction
    a reader needs and a single hash cannot carry.
    """
    listing = listing_for(trap)
    # The listing itself is versioned: a fingerprint from before a path was
    # added was composed over the shorter list, so read the list from the same
    # revision as the files.
    rel = listing.relative_to(ROOT).as_posix()
    raw_text = read_at(rel, at).decode("utf-8")
    groups: dict[str, list[str]] = {}
    current = DEFAULT_GROUP
    for raw in raw_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].strip() or DEFAULT_GROUP
            groups.setdefault(current, [])
            continue
        groups.setdefault(current, []).append(line)
    return {name: sorted(paths) for name, paths in groups.items() if paths}


def surface_paths(trap: str, at: str | None = None) -> list[str]:
    """Every listed path, group headers removed, in the one order that hashes."""
    flat: list[str] = []
    for paths in surface_groups(trap, at).values():
        flat.extend(paths)
    return sorted(flat)


def fingerprint(trap: str, at: str | None = None) -> tuple[str, list[dict[str, str]]]:
    """Overall fingerprint plus per-member group, and the overall is unchanged.

    The composition deliberately ignores groups: it walks the flat sorted path
    list exactly as before, so adding headers to a listing does not move the
    number. That property is what makes this adoptable - if declaring a group
    restamped everything, landing it would cause the failure it fixes - and it
    is asserted by
    `test_declaring_surface_groups_does_not_move_the_fingerprint`.

    Per-group digests are a second reading of the same bytes, reported beside
    the overall rather than replacing it.
    """
    owner = {path: group
             for group, paths in surface_groups(trap, at).items()
             for path in paths}
    members = []
    binding = hashlib.sha256()
    for path in surface_paths(trap, at):
        digest = digest_at(path, at)
        binding.update(path.encode("utf-8"))
        binding.update(b"\0")
        binding.update(digest.encode("ascii"))
        binding.update(b"\n")
        members.append({"path": path, "sha256": digest,
                        "group": owner.get(path, DEFAULT_GROUP)})
    return binding.hexdigest(), members


def group_fingerprints(trap: str, at: str | None = None) -> dict[str, str]:
    """Short digest per group, composed the same way the overall is."""
    digests = {}
    for group, paths in surface_groups(trap, at).items():
        binding = hashlib.sha256()
        for path in sorted(paths):
            binding.update(path.encode("utf-8"))
            binding.update(b"\0")
            binding.update(digest_at(path, at).encode("ascii"))
            binding.update(b"\n")
        digests[group] = binding.hexdigest()[:SHORT]
    return digests


def stamp(trap: str, at: str | None = None) -> str:
    """The paste-ready stamp for a result row.

    Groups ride inside the stamp, sorted by name so the same bytes always
    produce the same text. The overall short hash stays first and stays what
    `current` means; the group digests are the part that keeps answering
    "which half moved" after the resolving commit is gone.
    """
    full, _ = fingerprint(trap, at)
    digests = group_fingerprints(trap, at)
    if len(digests) > 1:
        parts = " ".join(f"{name}:{digest}"
                         for name, digest in sorted(digests.items()))
        return f"[surface {full[:SHORT]} {parts}]"
    return f"[surface {full[:SHORT]}]"


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
                        "stamp": stamp(trap), "members": members}

    if args.json:
        print(json.dumps(report, indent=2))
        return 0
    for trap, record in report.items():
        label = f"{trap}: " if len(report) > 1 else ""
        print(f"{label}{record['stamp']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
