#!/usr/bin/env python3
"""PreToolUse[Write|Edit] gate: a managed HOME file is deployment output, not source.

Every file `scripts/deployment-manifest.tsv` maps is written by
`scripts/sync.sh` from a source in the checkout. Editing the HOME copy produces a
change that looks applied, passes nothing, and is silently reverted by the next
deploy - and `weekly-integrity` only notices it once a week, as drift, after the
edit has already been reported as done. This closes that window at the moment of
the write, which is the only moment the right source is still obvious.

It exists because it happened: on 2026-08-19 a contract clause was written into
`~/.claude/CLAUDE.md` instead of `main/claude/CLAUDE.contract.md`, by a session
that had read the manifest the day before. Knowing the rule was not the missing
part; checking at the moment of the write was.

Exit 0 allows, exit 2 blocks and returns stderr to the model - the same contract
as `leaf-redispatch`.

Scope, and why it is not wider:

- **Wholesale rows only.** A three-column row is merged, so its target holds
  machine state this repo never authors (`~/.claude/settings.json`,
  `~/.codex/config.toml`), and a local key belongs there. The one merged row with
  repo-owned children is `.agents/skills`, whose owners are named in
  `INSTALLED.txt`; those children are covered and the rest of the directory is
  not, which is what lets an unmanaged skill be edited in place.
- **Both the literal and the resolved path.** `~/.claude/skills/<name>` is a
  symlink into `~/.agents/skills/<name>`, so a write through it lands on managed
  bytes under a path the manifest does not list.
- **Fail open when the manifest cannot be read.** A gate that cannot evaluate its
  condition must not answer anyway: no checkout, no manifest, or a malformed one
  means every unrelated edit in every session would be refused. It says so on
  stderr instead. The condition it does evaluate fails closed.
"""
from __future__ import annotations

import json
import os
import sys

try:  # Observability must never be able to break the boundary it observes.
    import denial_log
except Exception:  # noqa: BLE001
    denial_log = None

WRITING_TOOLS = {"Write", "Edit", "NotebookEdit"}
PATH_FIELDS = ("file_path", "notebook_path")


def resolve_harness_repo() -> str:
    """Same resolution order as `weekly-integrity`: env, deployment marker, fallback."""
    configured = os.environ.get("AGENT_HARNESS_REPO")
    if configured:
        return os.path.expanduser(configured)
    marker = os.path.expanduser("~/.agents/skills/.agent-harness-source")
    try:
        with open(marker, encoding="utf-8") as stream:
            marked = stream.readline().strip()
    except OSError:
        marked = ""
    return os.path.expanduser(marked or "~/WorkSpace/agent-harness")


def managed_targets(repo: str) -> dict[str, str]:
    """HOME-absolute target -> repo-relative source, for targets this repo owns whole."""
    manifest = os.path.join(repo, "scripts", "deployment-manifest.tsv")
    owned: dict[str, str] = {}
    home = os.path.expanduser("~")
    with open(manifest, encoding="utf-8") as stream:
        for raw in stream:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            fields = line.split("\t")
            if len(fields) not in (2, 3) or not all(fields):
                raise ValueError("malformed deployment manifest line")
            source, target = fields[:2]
            mode = fields[2] if len(fields) == 3 else ""
            if not target.startswith((".agents/", ".claude/", ".codex/")):
                raise ValueError("unsafe deployment manifest target")
            if mode:
                continue                      # merged: holds machine state too
            owned[os.path.join(home, target)] = source
    if not owned:
        raise ValueError("deployment manifest lists no wholesale target")

    # The one merged row with repo-owned children. `INSTALLED.txt` is the
    # allowlist sync itself uses, so an unmanaged skill beside them stays free.
    shared = os.path.join(home, ".agents", "skills")
    try:
        with open(os.path.join(repo, "main/.agents/skills/INSTALLED.txt"),
                  encoding="utf-8") as stream:
            names = [name.strip() for name in stream if name.strip()]
    except OSError:
        names = []
    for name in names:
        if "/" in name or name in ("", ".", ".."):
            continue
        owned[os.path.join(shared, name)] = f"main/.agents/skills/{name}"
    return owned


def offending(path: str, owned: dict[str, str]) -> tuple[str, str] | None:
    """The managed target this write lands on, literal or through a symlink.

    Both sides are compared in both forms. Resolving only the written path is
    not enough and the test proves it: on macOS a temporary HOME under `/var`
    resolves to `/private/var`, so a resolved candidate never matched an
    unresolved target and the link case returned "allowed". Any HOME that is
    itself a link has the same shape.
    """
    if not path:
        return None
    expanded = os.path.expanduser(path)
    candidates = {os.path.abspath(expanded), os.path.realpath(expanded)}
    for target, source in owned.items():
        for form in {target, os.path.realpath(target)}:
            for candidate in candidates:
                if candidate == form or candidate.startswith(form + os.sep):
                    return target, source
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        return 0
    if not isinstance(payload, dict) or payload.get("tool_name") not in WRITING_TOOLS:
        return 0
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0
    path = ""
    for field in PATH_FIELDS:
        value = tool_input.get(field)
        if isinstance(value, str) and value:
            path = value
            break
    if not path:
        return 0

    repo = resolve_harness_repo()
    try:
        owned = managed_targets(repo)
    except (OSError, ValueError) as error:
        sys.stderr.write(
            f"[managed-target-guard] not enforced: cannot read the deployment "
            f"manifest under {repo} ({error}). Managed HOME files are unguarded "
            "until the checkout is reachable; set AGENT_HARNESS_REPO if it moved.\n"
        )
        return 0

    hit = offending(path, owned)
    if hit is None:
        return 0
    target, source = hit
    sys.stderr.write(
        f"[managed-target-guard] blocked: {path} is deployment output. "
        f"{target} is written by scripts/sync.sh from {source}; an edit here is "
        "reverted by the next deploy and is tested by nothing. Edit "
        f"{source} in the checkout, run the suite, then deploy with "
        "scripts/sync.sh --apply (the user runs that step).\n"
    )
    if denial_log is not None:
        denial_log.record("managed-target-guard", "wrote-to-managed-target",
                          payload, caller=path)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
