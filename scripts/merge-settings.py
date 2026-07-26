#!/usr/bin/env python3
"""Ownership-aware merge of the repo's settings.json into a deployed one.

A wholesale copy is wrong for this file because three writers share it: this
repo (hooks, permissions, statusLine), Claude Code itself (`/model`, `/effort`),
and third-party installers that register their own hooks. Replacing the file
deletes the other two; refusing to write it (the previous `--accept-settings-
overwrite` abort) means the repo's own updates never land.

The merge resolves that by ownership rather than by position:

  * A hook group is *owned* when any command in it matches OWNED_HOOK_PATTERNS.
    Owned groups are replaced wholesale by the repo's, so a stale command is
    updated rather than duplicated. Foreign groups are preserved verbatim, and
    a foreign hook found inside an owned group is rescued into its own group
    rather than dropped.
  * Hook events the repo does not define at all are preserved untouched.
  * Lists elsewhere (notably permissions.allow) become a union: every repo
    entry is present, and entries only the machine has survive.
  * Top-level keys the repo does not define (`model`, `effortLevel`) survive.

The repo is the sole authority on its own entries and never an authority on
anyone else's. `--check` asserts that every group in a settings file is owned,
which is what keeps OWNED_HOOK_PATTERNS honest as hooks are added.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

# A hook belongs to this repo when its command matches one of these. Every
# group in main/claude/settings.json must match (enforced by --check and by
# the deployment tests), so adding a hook without extending this list fails
# loudly instead of silently making the new hook un-updatable.
OWNED_HOOK_PATTERNS = (
    "$HOME/.claude/hooks/",
    "rtk hook claude",
)


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def hook_commands(group: dict) -> list[str]:
    return [h.get("command", "") for h in group.get("hooks", [])
            if isinstance(h, dict)]


def is_owned_command(command: str) -> bool:
    return any(pattern in command for pattern in OWNED_HOOK_PATTERNS)


def is_owned_group(group: dict) -> bool:
    return any(is_owned_command(command) for command in hook_commands(group))


def split_foreign_hooks(group: dict) -> list[dict]:
    """Foreign hooks sitting inside an owned group, as standalone groups.

    Replacing an owned group would otherwise delete a third-party hook that had
    been appended into it. Rescuing preserves it without letting it block the
    repo's own update.
    """
    foreign = [h for h in group.get("hooks", [])
               if isinstance(h, dict) and not is_owned_command(h.get("command", ""))]
    if not foreign:
        return []
    rescued = {k: v for k, v in group.items() if k != "hooks"}
    rescued["hooks"] = foreign
    return [rescued]


def merge_hooks(repo: dict, deployed: dict) -> dict:
    merged: dict[str, list] = {}
    for event in list(repo) + [e for e in deployed if e not in repo]:
        repo_groups = repo.get(event, [])
        deployed_groups = deployed.get(event, [])
        preserved: list[dict] = []
        for group in deployed_groups:
            if not isinstance(group, dict):
                preserved.append(group)
            elif is_owned_group(group):
                preserved.extend(split_foreign_hooks(group))
            else:
                preserved.append(group)
        groups = list(repo_groups) + preserved
        if groups:
            merged[event] = groups
    return merged


def merge_value(repo, deployed, managed: dict, path: str = "",
                retracted: list | None = None):
    if isinstance(repo, dict) and isinstance(deployed, dict):
        merged = copy.deepcopy(deployed)
        for key, value in repo.items():
            child = f"{path}.{key}" if path else key
            merged[key] = (merge_value(value, deployed[key], managed, child, retracted)
                           if key in deployed else value)
        return merged
    if isinstance(repo, list) and isinstance(deployed, list):
        # The repo's entries always land. A deployed entry the repo no longer
        # declares is kept only when the repo never put it there: a plain union
        # cannot tell a machine-added permission from one this repo granted and
        # has since withdrawn, so removing a grant from source would leave it
        # deployed forever.
        wanted = {canonical(item) for item in repo}
        previously_ours = set(managed.get(path, []))
        kept = []
        for item in deployed:
            key = canonical(item)
            if key in wanted:
                continue  # already carried by the repo's own entries
            if key in previously_ours:
                if retracted is not None:
                    retracted.append(f"{path}: {key}")
                continue
            kept.append(item)
        return list(repo) + kept
    return repo


def managed_entries(repo, path: str = "", into: dict | None = None) -> dict:
    """Canonical forms of every list entry this repo contributes, by path.

    Written after a successful merge so the next one can distinguish "the repo
    withdrew this" from "the machine added this". Absent provenance means
    unknown, never machine-owned — an upgrade must not retroactively delete.
    """
    into = {} if into is None else into
    if isinstance(repo, dict):
        for key, value in repo.items():
            managed_entries(value, f"{path}.{key}" if path else key, into)
    elif isinstance(repo, list) and path:
        into[path] = [canonical(item) for item in repo]
    return into


def merge_settings(repo: dict, deployed: dict, managed: dict | None = None,
                   retracted: list | None = None) -> dict:
    merged = merge_value(
        {k: v for k, v in repo.items() if k != "hooks"},
        {k: v for k, v in deployed.items() if k != "hooks"},
        managed or {}, "", retracted,
    )
    if "hooks" in repo or "hooks" in deployed:
        merged["hooks"] = merge_hooks(repo.get("hooks", {}), deployed.get("hooks", {}))
    return merged


def preserved_report(repo: dict, merged: dict) -> list[str]:
    """What survived that the repo does not define - the merge's whole point."""
    kept = [key for key in merged if key not in repo and key != "hooks"]
    lines = [f"kept machine key: {key}" for key in sorted(kept)]
    for event, groups in merged.get("hooks", {}).items():
        foreign = [g for g in groups if isinstance(g, dict) and not is_owned_group(g)]
        if foreign:
            lines.append(f"kept {len(foreign)} foreign hook group(s) in {event}")
    return lines


def write_managed(path: Path, repo: dict, dry_run: bool) -> None:
    """Record what the repo owns now, so the next merge can retract removals."""
    if dry_run:
        return
    try:
        path.write_text(
            json.dumps(managed_entries({k: v for k, v in repo.items()
                                        if k != "hooks"}), indent=2) + "\n",
            encoding="utf-8")
    except OSError as exc:
        # Losing provenance costs a future retraction, never the merge itself.
        print(f"  warning: could not record managed entries: {exc}",
              file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", type=Path)
    parser.add_argument("deployed", type=Path, nargs="?")
    parser.add_argument("--managed", type=Path, default=None,
                        help="provenance sidecar; defaults to a dotfile beside "
                             "the deployed file")
    parser.add_argument("--check", action="store_true",
                        help="verify every hook group in `repo` is owned")
    parser.add_argument("--dry-run", action="store_true",
                        help="report the merge without writing")
    parser.add_argument("--verify", action="store_true",
                        help="exit non-zero if a merge would still change the "
                             "deployed file; the post-sync parity check for "
                             "merged targets, which can never be byte-equal")
    args = parser.parse_args()

    repo = json.loads(args.repo.read_text(encoding="utf-8"))

    if args.check:
        unowned = [
            f"{event}[{index}]: {hook_commands(group)}"
            for event, groups in repo.get("hooks", {}).items()
            for index, group in enumerate(groups)
            if not is_owned_group(group)
        ]
        if unowned:
            print("ERROR: hook groups not matched by OWNED_HOOK_PATTERNS; the "
                  "merge could not update them on deploy:", file=sys.stderr)
            for line in unowned:
                print(f"  - {line}", file=sys.stderr)
            return 1
        print(f"ownership ok: every hook group in {args.repo.name} is owned")
        return 0

    if args.deployed is None:
        parser.error("deployed path is required unless --check is given")

    if not args.deployed.exists():
        if args.verify:
            print(f"ERROR: merged target missing: {args.deployed}", file=sys.stderr)
            return 1
        if args.dry_run:
            print(f"[dry-run] no deployed settings; would install {args.repo}")
            return 0
        args.deployed.parent.mkdir(parents=True, exist_ok=True)
        args.deployed.write_text(json.dumps(repo, indent=2) + "\n", encoding="utf-8")
        print(f"installed fresh settings: {args.deployed}")
        return 0

    deployed = json.loads(args.deployed.read_text(encoding="utf-8"))
    managed_path = args.managed or args.deployed.with_name(
        f".{args.deployed.stem}-managed.json")
    try:
        managed = json.loads(managed_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        managed = {}  # no provenance recorded yet: keep everything
    retracted: list[str] = []
    merged = merge_settings(repo, deployed, managed, retracted)
    report = preserved_report(repo, merged) + [
        f"retracted (repo no longer grants it): {line}" for line in retracted]

    if merged == deployed:
        print("settings already merged; no change")
        write_managed(managed_path, repo, args.dry_run)
        return 0
    if args.verify:
        print(f"ERROR: {args.deployed} still lacks repo-declared settings after "
              "sync; a merge would change it", file=sys.stderr)
        return 1
    for line in report:
        print(f"  {line}")
    if args.dry_run:
        print(f"[dry-run] would merge {args.repo} -> {args.deployed}")
        return 0
    args.deployed.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    write_managed(managed_path, repo, dry_run=False)
    print(f"merged settings -> {args.deployed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
