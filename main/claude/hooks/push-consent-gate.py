#!/usr/bin/env python3
"""PreToolUse[Bash] gate: `git push` runs only when the user armed it, once.

Why this exists. On 2026-09-06 the user approved one push ("push, then
continue") and the session pushed five more times over the following hours
without asking. The rule was resident the whole time - outward-facing actions
confirm each time, approval in one context does not extend to the next - and
the user said the mistake had recurred many times. A resident reminder does not
hold under a long task; a gate at the action site does. So the rule moves here.

How consent is expressed. The user arms exactly one push by creating the
sentinel below outside the assistant's tool surface (for example `! touch
~/.claude/telemetry/push-consent-armed` at the prompt). A push consumes it. A
second push needs a second arming. The sentinel expires after ARMED_TTL_S so a
forgotten arming cannot leak into a later session, and a stale one is removed
when found rather than left to be read as consent.

What the gate refuses. Any Bash command that contains a `git push` invocation
in any segment - `/usr/bin/git push`, `git -C repo push`, `cd x && git push`,
`GIT_DIR=.. git push`, force pushes, dry runs - when no fresh sentinel exists.
And any Bash command that names the sentinel at all: arming is the user's move,
and a gate the gated party can arm is not a gate. Everything else passes, and
so does unparseable input, because the hook cannot establish that it is a Bash
call at all (the same rule `leaf-redispatch` follows). Once a push is
established without consent, the boundary fails closed.

Exit 0 allows; exit 2 blocks and returns stderr to the model. Denials are
recorded through `denial_log` where it is importable, never fatally.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import sys
import time
from pathlib import Path

SENTINEL_NAME = "push-consent-armed"
ARMED_TTL_S = 30 * 60

try:  # Observability must never be able to break the boundary it observes.
    import denial_log
except Exception:  # noqa: BLE001
    denial_log = None


def sentinel_path() -> Path:
    return Path.home() / ".claude" / "telemetry" / SENTINEL_NAME


# Segments end where the shell would start another command. Redirections are
# left inside a segment: `git push 2>&1 | tail` splits on the pipe only.
SEGMENT_SPLIT = re.compile(r"\|\||&&|;|\||\n")


def _words(segment: str) -> list[str]:
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        return segment.split()


def is_git_push(command: str) -> bool:
    """True when any segment invokes git's `push` subcommand.

    Word-based rather than one regex: `echo push`, `git stash push` and a
    commit message that mentions pushing are not pushes, while `git -C repo
    push`, `/usr/bin/git push` and `VAR=x git push` are.
    """
    for segment in SEGMENT_SPLIT.split(command):
        words = _words(segment)
        for index, word in enumerate(words):
            if os.path.basename(word) != "git":
                continue
            rest = words[index + 1:]
            skip = 0
            for token in rest:
                if skip:
                    skip -= 1
                    continue
                if token in ("-C", "-c", "--git-dir", "--work-tree", "--namespace",
                             "--exec-path", "--super-prefix", "--config-env"):
                    skip = 1
                    continue
                if token.startswith("-"):
                    continue
                if token == "push":
                    return True
                break
    return False


def names_sentinel(command: str) -> bool:
    return SENTINEL_NAME in command


def deny(reason: str, payload: dict, detail: str, command: str = "") -> int:
    sys.stderr.write(
        "[push-consent-gate] blocked: " + detail + "\n"
        "Every push is its own decision. Commit locally, tell the user what is "
        "ready to push, and let them arm one push with\n"
        "    ! touch ~/.claude/telemetry/push-consent-armed\n"
        "at the prompt; the next push consumes it.\n")
    if denial_log is not None:
        try:
            denial_log.record("push-consent-gate", reason, payload,
                              command=command[:200] or None)
        except Exception:  # noqa: BLE001
            pass
    return 2


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        return 0
    if not isinstance(payload, dict) or payload.get("tool_name") != "Bash":
        return 0
    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "") if isinstance(tool_input, dict) else ""
    if not command:
        return 0

    if names_sentinel(command):
        return deny("assistant-tried-to-arm", payload,
                    "the command names the consent sentinel; only the user arms a push.",
                    command)
    if not is_git_push(command):
        return 0

    sentinel = sentinel_path()
    if sentinel.exists():
        age = time.time() - sentinel.stat().st_mtime
        try:
            sentinel.unlink()
        except OSError:
            pass
        if age <= ARMED_TTL_S:
            return 0
        return deny("push-armed-but-stale", payload,
                    f"the consent sentinel was {int(age // 60)} minutes old (limit "
                    f"{ARMED_TTL_S // 60}); it has been removed and this push was not made.",
                    command)
    return deny("push-without-consent", payload,
                "a git push with no armed consent.", command)


if __name__ == "__main__":
    raise SystemExit(main())
