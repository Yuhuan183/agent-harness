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

What the gate refuses. Any Bash command that runs a `git push` anywhere the
shell would - `/usr/bin/git push`, `git -C repo push`, `cd x && git push`,
`GIT_DIR=.. git push`, force pushes, dry runs, and the spellings that only
become a push once the shell has read them: a subshell or substitution glued to
`git`, a push handed to `sh -c` or `eval`, a subcommand split by quotes or an
escape, or one that comes out of an expansion - when no fresh sentinel exists.
A subcommand the shell alone can resolve (`git $C`) is refused the same way,
with its own reason. What stays out of reach needs the argv boundary rather
than the text: a git alias (`git -c alias.p=push p`), a wrapper script, a PATH
shadow. The settings prefilter normalizes quotes and escapes and hands over
any expansion, for the same reason the commit gate's prefilter does.
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


# Characters that end a word and start another command, outside quotes.
SEPARATOR_CHARS = ";&|()\n"
# A marker for text only the shell will produce. No command line contains it,
# so it cannot be typed into place to fake or hide one.
RUNTIME = "\x00"
GIT_VALUE_OPTIONS = ("-C", "-c", "--git-dir", "--work-tree", "--namespace",
                     "--exec-path", "--super-prefix", "--config-env")
# Programs whose job is to run a command handed to them as text.
SHELL_RUNNERS = ("sh", "bash", "zsh", "dash", "ksh")
ASSIGNMENT = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=(.*)", re.DOTALL)
EXPANSION = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")
MAX_DEPTH = 5


def _substitution(command: str, start: int, closer: str) -> tuple[str, int]:
    """The body of a `$(...)` or backtick substitution, and where it ends."""
    depth, index = 1, start
    while index < len(command):
        char = command[index]
        if char == "\\":
            index += 2
            continue
        if closer == ")" and char == "(":
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return command[start:index], index + 1
        index += 1
    return command[start:], index


def _scan(command: str) -> tuple[list[str], list[str]]:
    """Words and separators the way the shell reads them, plus every body it runs.

    `shlex` gets the quotes right but forgets which ones they were, and the
    difference decides this gate: a backtick inside single quotes is text, the
    same backtick inside double quotes runs a command. So a small scanner keeps
    that one distinction: single-quoted text is inert, and a `$(...)` or
    backtick outside it is both a body to read and a word only the shell knows.
    """
    tokens: list[str] = []
    bodies: list[str] = []
    word: list[str] = []
    started = False
    quote = ""
    index = 0

    def end_word() -> None:
        nonlocal word, started
        if started:
            tokens.append("".join(word))
        word, started = [], False

    while index < len(command):
        char = command[index]
        if quote == "'":
            if char == "'":
                quote = ""
            else:
                word.append(char)
            index += 1
            continue
        if char == "\\" and index + 1 < len(command):
            word.append(command[index + 1])
            started = True
            index += 2
            continue
        if char == "`" or command.startswith("$(", index):
            closer, skip = ("`", 1) if char == "`" else (")", 2)
            body, index = _substitution(command, index + skip, closer)
            bodies.append(body)
            word.append(RUNTIME)
            started = True
            continue
        if quote == '"':
            if char == '"':
                quote = ""
            else:
                word.append(char)
            index += 1
            continue
        if char in "'\"":
            quote, started = char, True
        elif char in SEPARATOR_CHARS:
            end_word()
            tokens.append(char)
        elif char.isspace():
            end_word()
        else:
            word.append(char)
            started = True
        index += 1
    end_word()
    return tokens, bodies


def _is_runtime(token: str) -> bool:
    return RUNTIME in token or "$" in token


def git_push_kind(command: str, depth: int = 0) -> str | None:
    """`"push"` when some command runs git's push, `"runtime"` when the shell decides.

    Read word by word rather than by one regex: `echo push`, `git stash push`
    and a commit message that mentions pushing are not pushes, while `git -C
    repo push`, `/usr/bin/git push`, `(git push)`, `bash -c 'git push'`,
    `git pu''sh` and `E=; git pu${E}sh` are. A subcommand that only exists once
    the shell expands it (`git $C`) cannot be read at all, and a gate that
    allowed what it could not read would be the bypass (2026-09-30 review).
    """
    if depth > MAX_DEPTH:
        # Unread from here on. Only text that could still become a push is
        # refused: one that names it once quotes and escapes are gone, or that
        # holds an expansion the shell may turn into one.
        flat = re.sub(r"[\"'\\\\]", "", command)
        return "runtime" if "push" in flat or "$" in flat or "`" in flat else None
    tokens, bodies = _scan(command.replace("\\\n", ""))
    for body in bodies:
        kind = git_push_kind(body, depth + 1)
        if kind:
            return kind
    values = dict(os.environ)
    for token in tokens:
        match = ASSIGNMENT.fullmatch(token)
        if match and not _is_runtime(match.group(2)):
            values[match.group(1)] = match.group(2)
    tokens = [EXPANSION.sub(lambda m: values.get(m.group(1) or m.group(2), m.group(0)), t)
              for t in tokens]
    for index, token in enumerate(tokens):
        rest = tokens[index + 1:]
        segment = []
        for item in rest:
            if item in SEPARATOR_CHARS:
                break
            segment.append(item)
        name = os.path.basename(token)
        if name in SHELL_RUNNERS:
            for position, flag in enumerate(segment[:-1]):
                if flag.startswith("-") and not flag.startswith("--") and "c" in flag:
                    kind = git_push_kind(segment[position + 1], depth + 1)
                    if kind:
                        return kind
                    break
        elif name == "eval":
            kind = git_push_kind(" ".join(segment), depth + 1)
            if kind:
                return kind
        elif name == "git":
            skip = False
            for item in segment:
                if skip:
                    skip = False
                elif item in GIT_VALUE_OPTIONS:
                    skip = True
                elif item.startswith("-"):
                    continue
                elif item == "push":
                    return "push"
                elif _is_runtime(item):
                    return "runtime"
                else:
                    break
        elif _is_runtime(token) and segment[:1] == ["push"]:
            return "runtime"
    return None


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
    kind = git_push_kind(command)
    if kind is None:
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
    if kind == "runtime":
        return deny("push-subcommand-at-runtime", payload,
                    "a git subcommand the shell only resolves when it runs, with no "
                    "armed consent; spell the subcommand literally.", command)
    return deny("push-without-consent", payload,
                "a git push with no armed consent.", command)


if __name__ == "__main__":
    raise SystemExit(main())
