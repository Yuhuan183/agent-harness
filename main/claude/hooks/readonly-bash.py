#!/usr/bin/env python3
"""PreToolUse[Bash] boundary for the read-only reviewer roles.

Claude Code has no per-agent sandbox: `sandbox.*` is session-level and every
subagent inherits the parent's configuration, so the Codex twins' enforced
`sandbox_mode = "read-only"` has no frontmatter equivalent here. Frontmatter
can only grant or withhold the whole Bash tool, and a `verifier` without Bash
cannot reproduce anything — which is the one thing its contract requires it to
do before believing a test report.

So the boundary is drawn here instead, on the identity the payload carries:
`agent_type` is the subagent's frontmatter name and is absent for main-session
calls (verified against Claude Code 2.1.220).

The list is an allowlist, and everything else is denied. A denylist over shell
strings is unclosable — `rm` has `find -delete`, `>` has `tee`, and anything at
all has `python -c` — so the only defensible default is refusal. A reviewer
that needs a command outside it hands that command back to the caller, which
its contract already prescribes for checks that inherently write.

Exit 0 allows; exit 2 blocks and returns stderr to the model. Unparseable
input is denied for these roles rather than waved through: a boundary that
fails open is not a boundary.
"""
from __future__ import annotations

import json
import re
import shlex
import sys

GUARDED_ROLES = ("verifier", "plan-verifier", "security-reviewer", "explore")

# Command heads that only ever read. `find` is absent on purpose (-delete,
# -exec), as are awk/python/perl/sh (arbitrary writes) and tee/xargs.
READ_ONLY = {
    "git", "grep", "rg", "sed", "ls", "cat", "head", "tail", "wc", "file",
    "stat", "basename", "dirname", "realpath", "readlink", "pwd", "echo",
    "printf", "which", "command", "type", "jq", "diff", "cmp", "sort", "uniq",
    "cut", "tr", "column", "date", "env", "true", "false", "test",
}
# git is only read-only for these subcommands. Anything with a writing form is
# out even when the reading form is the common one: `config --global`, bare
# `stash`, `worktree add`, `branch -d`, `tag -d` and `remote add` all mutate,
# and this hook does not parse deeply enough to tell them apart.
GIT_READ_ONLY = {
    "status", "diff", "log", "show", "grep", "blame", "rev-parse", "ls-files",
    "ls-tree", "cat-file", "describe", "shortlog", "for-each-ref",
    "merge-base", "check-ignore",
}
# `sed -i` and `sort -o` write; so does any redirection.
WRITE_FLAGS = {"sed": ("-i",), "sort": ("-o",), "git": (), "cp": (), "test": ()}
REDIRECT = re.compile(r"(?<![0-9<>])>{1,2}(?!&)|(?<![0-9])<>")
SEPARATORS = {"&&", "||", ";", "|", "&"}


def deny(reason: str) -> int:
    sys.stderr.write(
        f"[readonly-bash] blocked: {reason}\n"
        "This role's isolation boundary is read-only. If a meaningful check "
        "inherently writes, return the exact command for the caller to run "
        "instead of running it here.\n")
    return 2


def offending(command: str) -> str | None:
    """Return why the command is not provably read-only, or None if it is."""
    if REDIRECT.search(command):
        return "output redirection"
    if "`" in command or "$(" in command:
        return "command substitution (its contents cannot be checked here)"
    try:
        tokens = shlex.split(command, comments=True)
    except ValueError as exc:
        return f"unparseable command ({exc})"
    expect_head = True
    for index, token in enumerate(tokens):
        if token in SEPARATORS:
            expect_head = True
            continue
        if not expect_head:
            continue
        expect_head = False
        head = token.rsplit("/", 1)[-1]
        if head == "rtk":  # output filter, never the acting command
            expect_head = True
            continue
        if "=" in head and not head.startswith("-"):
            expect_head = True  # leading VAR=value assignment
            continue
        if head not in READ_ONLY:
            return f"{head!r} is not on the read-only allowlist"
        rest = tokens[index + 1:]
        if head == "git":
            sub = next((t for t in rest if not t.startswith("-")), "")
            if sub not in GIT_READ_ONLY:
                return f"git subcommand {sub!r} is not known to be read-only"
        for flag in WRITE_FLAGS.get(head, ()):
            if any(t == flag or t.startswith(flag) for t in rest):
                return f"{head} {flag} writes"
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        return 0  # not our payload to judge; other gates still apply
    if payload.get("tool_name") != "Bash":
        return 0
    if payload.get("agent_type") not in GUARDED_ROLES:
        return 0
    command = (payload.get("tool_input") or {}).get("command")
    if not isinstance(command, str):
        return deny("no command string to inspect")
    reason = offending(command)
    return deny(reason) if reason else 0


if __name__ == "__main__":
    raise SystemExit(main())
