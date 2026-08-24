#!/usr/bin/env python3
"""Has any upstream this repo distils from moved past its recorded pin? Reports; never fails.

Why this exists. `upstream-recheck.sh` answers a different question and answers
it well: do the bytes a SHA pins still hash to what the ledger says. By design
that stays green when upstream moves, because a SHA pins content. So nothing
here asked the other question - is the pin still what upstream serves - for any
upstream at all.

The cost was paid on 2026-08-21. `mattpocock/skills` had moved twelve commits
past the recorded pin four days earlier, and it was found only because somebody
went looking by hand. Three upstreams were rechecked that day, all three
manually, and the distillation skill had to declare "every other recheck is
manual" as a known limit. This is that limit closed for the first half of the
job: which upstreams moved, and by how much.

Derived from the `ATTRIBUTION.md` files rather than a list. Adding a distilled
skill extends this report the day its attribution lands, which is the property a
separate registry would lose the first time someone forgot to update it. The
parsing is deliberately tolerant: the five attributions in this repo state their
source in three different shapes (`**Source**:` plus `**Reviewed commit**:`,
`- 專案：` plus `- 蒸餾自：`, and a bare URL plus `- Commit:`), and normalising
them is a separate decision from being able to read them.

What it cannot tell you: whether a move matters. Twelve commits of punctuation
and one commit that deletes a rule look identical here. Reading the diff is the
next step and belongs to a person - see the `upstream-distillation` skill.

It also compares against the default branch, which for a marketplace-distributed
upstream is ahead of what the marketplace serves. `mattpocock/skills` read
`MOVED +2` the same hour its pin was advanced to the catalog's current SHA, and
both facts were true. For those, this report says "the repository moved"; whether
the *pin* moved is a question for the catalog.

Network: a fetch that fails is reported as unreachable, never as "not moved".
Those two must not look the same, which is the whole lesson above.

Usage:
    scripts/upstream-pin-report.py [--attributions DIR] [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = re.compile(r"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?(?=[)\s>/]|$)")
SHA = re.compile(r"\b([0-9a-f]{40})\b")
API = "https://api.github.com/repos/{repo}/compare/{base}...{head}"
# Enough to tell "our source tree moved" from "a chart was regenerated" without
# turning the line into a file list.
AREAS = 4


def parse_attributions(root: Path) -> list[dict]:
    """Every attribution that names a GitHub repository and a full commit.

    One entry per (repo, sha): `task-observer` ships the identical file twice,
    once per provider tree, and reporting the same upstream twice would read as
    two upstreams.
    """
    found: dict[tuple[str, str], dict] = {}
    for path in sorted(root.rglob("ATTRIBUTION.md")):
        text = path.read_text(encoding="utf-8")
        repo = REPO.search(text)
        sha = SHA.search(text)
        if not repo or not sha:
            continue
        key = (f"{repo.group(1)}/{repo.group(2)}", sha.group(1))
        entry = found.setdefault(key, {"repo": key[0], "pin": key[1], "skills": []})
        if path.parent.name not in entry["skills"]:
            entry["skills"].append(path.parent.name)
    return list(found.values())


def summarise(body: dict) -> dict:
    """Turn a compare response into the report's row.

    Split from the fetch so it can be tested without a network: the fetch has
    one interesting behaviour (a failure must never read as `current`) and this
    has another, and testing them together means testing neither.
    """
    if not isinstance(body, dict) or "ahead_by" not in body:
        return {"state": "unreachable",
                "detail": str(body.get("message") if isinstance(body, dict) else body)[:80]}
    # The same response already carries the file list, so "where did it move"
    # costs nothing extra - and it is the question that decides whether the move
    # is worth a recheck. On 2026-08-24 one upstream read `MOVED +3` and all
    # three commits were a bot refreshing a chart under `assets/`, which a count
    # alone cannot say. An absent list stays empty rather than being guessed at.
    areas: dict[str, int] = {}
    for changed in body.get("files") or []:
        name = changed.get("filename", "")
        head = name.split("/", 1)[0] + "/" if "/" in name else name
        if head:
            areas[head] = areas.get(head, 0) + 1
    commits = body.get("commits") or [{}]
    return {"state": "moved" if body["ahead_by"] else "current",
            "ahead": body["ahead_by"],
            "head": commits[-1].get("sha", "")[:8],
            "areas": areas,
            "since": (commits[0].get("commit", {})
                      .get("committer", {}).get("date", ""))[:10]}


def moved(repo: str, pin: str) -> dict:
    """How far the default branch is ahead of `pin`, or why we cannot say."""
    try:
        request = urllib.request.Request(
            API.format(repo=repo, base=pin, head="HEAD"),
            headers={"Accept": "application/vnd.github+json",
                     "User-Agent": "agent-harness-upstream-pin-report"})
        with urllib.request.urlopen(request, timeout=20) as response:
            body = json.load(response)
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as error:
        return {"state": "unreachable", "detail": str(error)[:80]}
    return summarise(body)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attributions", default=str(ROOT / "main"),
                        help="tree to scan for ATTRIBUTION.md (the suite uses it)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    entries = parse_attributions(Path(args.attributions))
    for entry in entries:
        entry.update(moved(entry["repo"], entry["pin"]))

    if args.json:
        print(json.dumps(entries, ensure_ascii=False, indent=2))
        return 0

    if not entries:
        print(f"no attribution naming a repository and a commit under "
              f"{args.attributions}")
        return 0
    print(f"{len(entries)} pinned upstream(s)\n")
    for entry in entries:
        skills = ", ".join(sorted(entry["skills"]))
        if entry["state"] == "moved":
            mark = f"MOVED +{entry['ahead']}"
            tail = f"  head {entry['head']}, first new commit {entry['since']}"
            areas = sorted(entry.get("areas", {}).items(),
                           key=lambda pair: (-pair[1], pair[0]))
            if areas:
                shown = ", ".join(f"{name} ({count})" for name, count in areas[:AREAS])
                if len(areas) > AREAS:
                    shown += f", +{len(areas) - AREAS} more"
                tail += f"\n{'':14s}touched {shown}"
        elif entry["state"] == "current":
            mark, tail = "current", ""
        else:
            mark, tail = "unreachable", f"  {entry['detail']}"
        print(f"  {mark:12s} {entry['repo']:34s} pin {entry['pin'][:8]}  ({skills}){tail}")
    if any(e["state"] == "moved" for e in entries):
        print("\nA move is not a reason to follow it, and for a "
              "marketplace-distributed upstream the default branch runs ahead of "
              "the served pin. Read the diff, classify every rule, advance the pin "
              "only after: see the upstream-distillation skill.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
