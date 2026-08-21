#!/usr/bin/env python3
"""Does running the suite change anything on this machine? Reports; never fails.

Why this exists. On 2026-08-20 the suite was found to have written 35,853
fixture denials into the developer's own `~/.claude/telemetry/denials.jsonl`,
over twelve days, because the gates resolve their log path from HOME and the
tests run those gates for real. That was found by hand, and only because someone
finally read the log. Nothing would have found it otherwise, and nothing would
find the next one.

So this is the check that would have. Snapshot the three managed trees, run the
suite, snapshot again, print the difference. A clean run prints nothing to act
on; a dirty run names the file.

Run it after adding a hook, a gate, or anything else that writes outside the
repository - not on every commit. It runs the whole suite, so it costs about as
much as one commit does, and the property it checks only changes when something
new starts writing.

Exclusions are the blind spot, so the count is printed. Volatile paths that
churn for reasons unrelated to the suite (caches, transcripts, debug logs, the
CLI's own history) are skipped; everything else is compared by size and mtime.
If a future bleed lands inside an excluded path this report will say nothing,
which is exactly why the excluded count is on screen rather than in this
docstring only.

`--command` generalises it: the question is always "what did running this change
outside the repository", and the suite is only the default answer worth having.

Usage:
    scripts/machine-state-check.py [--command CMD] [--trees A,B] [--json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TREES = ("~/.claude", "~/.agents", "~/.codex")
# Churns for its own reasons; comparing it would make every run dirty.
VOLATILE = ("/debug/", "/projects/", "/history.jsonl", "/daemon.log", "/cache/",
            "/paste-cache/", "/image-cache/", "/file-history/", "/statsig",
            "/1p_failed_events", "/.DS_Store", "/shell-snapshots/", "/todos/",
            "/ide/", "/jobs/", "/logs/", "/.integrity-last-run",
            "/.runtime-version-cache")


# Files at or below this are compared by content; larger ones by size and
# nanosecond mtime. Comparing small files by stat alone missed a same-size
# rewrite landing inside the same second (reproduced 2026-08-21) - which is
# exactly the shape of a state file whose counter or timestamp keeps its length.
# Content rather than mtime for those, so a touch that changes nothing does not
# read as a change. Hashing this tree costs about 2 seconds.
HASH_LIMIT = 1 << 20


def fingerprint(path: str, size: int, mtime_ns: int) -> tuple:
    if size > HASH_LIMIT:
        return (size, mtime_ns)
    try:
        with open(path, "rb") as handle:
            return ("h", hashlib.blake2b(handle.read(), digest_size=16).digest())
    except OSError:
        return (size, mtime_ns)


def snapshot(trees: tuple[str, ...]) -> tuple[dict[str, tuple], int]:
    state: dict[str, tuple] = {}
    skipped = 0
    for tree in trees:
        root = os.path.expanduser(tree)
        for dirpath, _, names in os.walk(root):
            for name in names:
                path = os.path.join(dirpath, name)
                if any(mark in path for mark in VOLATILE):
                    skipped += 1
                    continue
                try:
                    info = os.stat(path)
                except OSError:
                    continue
                state[path] = fingerprint(path, info.st_size, info.st_mtime_ns)
    return state, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trees", default=",".join(TREES),
                        help="comma-separated roots to watch")
    parser.add_argument("--command", default=None,
                        help="shell command to observe instead of the suite; "
                             "the question is always \"what did this change\"")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    trees = tuple(t.strip() for t in args.trees.split(",") if t.strip())
    before, skipped = snapshot(trees)
    if args.command:
        observed = subprocess.run(args.command, shell=True, cwd=ROOT,
                                  capture_output=True, text=True)
    else:
        observed = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", ".",
             "-p", "test_*.py"],
            cwd=ROOT / "main/claude/tests", capture_output=True, text=True)
    after, _ = snapshot(trees)

    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(p for p in set(before) & set(after) if before[p] != after[p])

    report = {
        "watched": len(before),
        "excluded": skipped,
        "observed_ok": observed.returncode == 0,
        "added": added,
        "removed": removed,
        "changed": changed,
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    print(f"看住 {len(before):,} 個檔案, 略過 {skipped:,} 個易變路徑")
    what = args.command or "套件"
    print(f"{what}: {'綠' if observed.returncode == 0 else '紅 - 下面的差異可能只是它沒跑完'}")
    if not (added or removed or changed):
        print(f"{what}跑完, 這台機器沒有任何改變." if what == "套件"
              else f"跑完 {what}, 這台機器沒有任何改變.")
        return 0
    for label, paths in (("新增", added), ("刪除", removed), ("改動", changed)):
        if paths:
            print(f"\n{label} {len(paths)}:")
            for path in paths[:20]:
                print(f"  {path}")
            if len(paths) > 20:
                print(f"  … 另外 {len(paths) - 20} 個")
    return 0


if __name__ == "__main__":
    sys.exit(main())
