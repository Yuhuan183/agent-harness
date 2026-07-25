#!/usr/bin/env python3
"""Section-level merge of a repo TOML fragment into a machine-owned TOML file.

`~/.codex/config.toml` holds machine state this repo must never author: GPT
model and effort, MCP servers, plugins, marketplaces, desktop settings, shell
environment policy, and per-project trust. It also holds the `[agents.*]`
registrations that decide whether the repo's leaf roles exist at all. Copying
the file over would destroy the former; leaving it to a manual step left six of
seven roles unregistered on this machine for an unknown length of time, with
nothing able to notice.

The merge is textual and section-scoped, deliberately:

  * Only sections whose name is the owned prefix or a child of it (`agents`,
    `agents.verifier`, ...) are written. Every other section, every comment,
    and every byte of formatting is preserved exactly.
  * An owned section already present is replaced body-and-all, so a stale
    description is corrected rather than duplicated.
  * An owned section that is absent is inserted next to its siblings.
  * A section under the owned prefix that the repo does not declare is
    preserved and reported, not deleted - it may be the user's own agent.

Re-serialising through a TOML writer was rejected: it would silently reformat
and strip the comments in a file the user edits by hand.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SECTION_RE = re.compile(r"^\s*\[\[?([^\]]+)\]\]?\s*(?:#.*)?$")


def parse_sections(text: str) -> list[tuple[str | None, list[str]]]:
    """Split into (section name, lines). A leading None section is the preamble."""
    sections: list[tuple[str | None, list[str]]] = []
    name: str | None = None
    body: list[str] = []
    for line in text.splitlines(keepends=True):
        match = SECTION_RE.match(line)
        if match:
            if name is not None or body:
                sections.append((name, body))
            name, body = match.group(1).strip(), [line]
        else:
            body.append(line)
    if name is not None or body:
        sections.append((name, body))
    return sections


def is_owned(name: str | None, prefix: str) -> bool:
    return name is not None and (name == prefix or name.startswith(prefix + "."))


def normalize(body: list[str]) -> list[str]:
    """Body ending in exactly one blank line, so sections stay separated."""
    while body and body[-1].strip() == "":
        body.pop()
    if body and not body[-1].endswith("\n"):
        body[-1] += "\n"
    return body + ["\n"]


def merge_toml(repo_text: str, deployed_text: str, prefix: str):
    repo_owned = [(n, b) for n, b in parse_sections(repo_text) if is_owned(n, prefix)]
    repo_names = [n for n, _ in repo_owned]
    deployed = parse_sections(deployed_text)
    deployed_names = {n for n, _ in deployed if n is not None}

    updated, preserved_foreign = [], []
    result: list[tuple[str | None, list[str]]] = []
    for name, body in deployed:
        if name in repo_names:
            repo_body = next(b for n, b in repo_owned if n == name)
            if "".join(body).strip() != "".join(repo_body).strip():
                updated.append(name)
            result.append((name, normalize(list(repo_body))))
        else:
            if is_owned(name, prefix):
                preserved_foreign.append(name)
            result.append((name, body))

    added = [(n, b) for n, b in repo_owned if n not in deployed_names]
    if added:
        # Keep the owned block together: insert after the last owned section.
        last_owned = max(
            (i for i, (n, _) in enumerate(result) if is_owned(n, prefix)),
            default=len(result) - 1,
        )
        # Guarantee the section before the insert point ends cleanly.
        if 0 <= last_owned < len(result):
            result[last_owned] = (result[last_owned][0],
                                  normalize(list(result[last_owned][1])))
        for offset, (name, body) in enumerate(added, start=1):
            result.insert(last_owned + offset, (name, normalize(list(body))))

    text = "".join("".join(body) for _, body in result)
    report = {
        "added": [n for n, _ in added],
        "updated": updated,
        "preserved_sections": len(result) - len(repo_owned),
        "preserved_foreign_owned": preserved_foreign,
    }
    return text, report


def describe(report: dict) -> list[str]:
    lines = []
    for name in report["added"]:
        lines.append(f"added section: [{name}]")
    for name in report["updated"]:
        lines.append(f"updated section: [{name}]")
    for name in report["preserved_foreign_owned"]:
        lines.append(f"kept non-repo section under owned prefix: [{name}]")
    lines.append(f"preserved {report['preserved_sections']} machine section(s) untouched")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", type=Path)
    parser.add_argument("deployed", type=Path)
    parser.add_argument("--prefix", default="agents",
                        help="top-level section this repo owns (default: agents)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verify", action="store_true",
                        help="exit non-zero if a merge would still change the file")
    args = parser.parse_args()

    repo_text = args.repo.read_text(encoding="utf-8")
    if not args.deployed.exists():
        if args.verify:
            print(f"ERROR: merged target missing: {args.deployed}", file=sys.stderr)
            return 1
        if args.dry_run:
            print(f"[dry-run] no deployed config; would create {args.deployed}")
            return 0
        args.deployed.parent.mkdir(parents=True, exist_ok=True)
        owned = [b for n, b in parse_sections(repo_text) if is_owned(n, args.prefix)]
        args.deployed.write_text("".join("".join(normalize(list(b))) for b in owned),
                                 encoding="utf-8")
        print(f"created config from owned sections: {args.deployed}")
        return 0

    deployed_text = args.deployed.read_text(encoding="utf-8")
    merged, report = merge_toml(repo_text, deployed_text, args.prefix)

    if merged == deployed_text:
        # Still name any non-repo section under the owned prefix: it is exactly
        # the content a future careless change would delete, so it should stay
        # visible on every run, not only on runs that happen to write.
        for name in report["preserved_foreign_owned"]:
            print(f"  kept non-repo section under owned prefix: [{name}]")
        print("config already merged; no change")
        return 0
    if args.verify:
        print(f"ERROR: {args.deployed} is missing repo-declared [{args.prefix}] "
              f"sections: added={report['added']} updated={report['updated']}",
              file=sys.stderr)
        return 1
    for line in describe(report):
        print(f"  {line}")
    if args.dry_run:
        print(f"[dry-run] would merge {args.repo} -> {args.deployed}")
        return 0
    args.deployed.write_text(merged, encoding="utf-8")
    print(f"merged config -> {args.deployed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
