#!/usr/bin/env python3
r"""PreToolUse[Bash] gate: a git commit only proceeds on a green test suite.

Motivation (2026-07-23): three times in one session a red suite was committed
because `unittest | tail` swallowed the exit code and `;` broke the chain.
Reminders did not fix it; this hook makes green-before-commit deterministic.

Scope: fires when the Bash command contains a `git commit` and any repository
the command can plausibly target carries test modules under `.claude/tests/`
or the harness bundle's canonical `main/claude/tests/`. The target set is the
payload `cwd` plus every `git -C <path>` and `cd <path>` operand in the command,
so repo-switching forms cannot dodge the gate. Other repos and non-commit
commands pass through untouched. Escape hatch for intentional red commits
(e.g. committing a failing reproduction): prefix the command with
`AGENT_SKIP_TEST_GATE=1 `.

Spellings that only become `git commit` in the shell (2026-07-28 .. 2026-07-29).
The gate reads the command as text while the shell reads it as a program, so
every construct that rewrites the text before execution is a way past a naive
substring match. Three classes, all of them reproduced against real commits:

  quoting/continuations  `g'i't com''mit`, `git com\` + NL + `mit`
  parameter expansion    `E=; g${E}it com${E}mit`, `C=commit; git $C`
  substitution           `$(echo git) commit`, `` `echo git commit` ``

The first class is handled by deleting quote characters and folding
continuations; the other two by deleting the expansion spans. Deletion (never
substitution) keeps detection monotone: dropping characters can only bring a
match closer, and none of the deleted characters appear in `git` or `commit`.
A match in *any* of the copies gates the command, so a spelling that hides in
one still fires from another.

What deletion cannot recover is a subcommand that exists only at run time:
`git $C` normalizes to `git`, which is not a commit and not not-a-commit. That
one is decided structurally instead - if an expansion sits in the subcommand
slot of a `git` invocation, the command is gated. `git log $(git rev-parse x)`
keeps its visible subcommand and stays untouched, so the fail-closed case is
narrow rather than "any command containing a dollar sign".

Two more classes came out of the next review (2026-07-29), both reproduced: the
*executable* can come from an expansion (`G=git; $G commit`), and so can the
*repo being committed to* (`git -C "$R" commit`, `cd "$R" && git commit`). The
copies above cannot see either, and the second one is worse than a missed
match: COMMIT_RE fires, then the target resolves to nothing and the gate exits
0 having checked no suite at all.

Values come first: an assignment in the same command carries its value right
there, and a name exported by an earlier command is in this hook's own
environment, so both are substituted into a further copy. That turns the
ordinary spelling of both classes back into a literal. What survives is
decided structurally - an unknown executable in command position with `commit`
among its words is gated, and a commit-shaped command whose target still holds
an expansion is *blocked with a reason*, because a target the gate could not
resolve is a check that did not run, not a check that passed.

The residue is stated instead of hidden: `G=git; C=commit; $G $C` puts neither
word anywhere and neither value in reach, and gating it means gating every
`$A $B`. Only enforcement at the argv boundary - a `git` that reads its own
arguments after the shell is done with them - closes that class, and that is a
deployment decision rather than a parsing one.

The settings prefilter cannot do any of this in a `case` glob, so it hands over
whenever the payload carries an expansion at all and lets this module decide;
normalizing in only one of the two places is what left `g'i't com''mit`
unreachable while this module was already able to catch it.

Exit 0 = allow; exit 2 = block, stderr goes back to the model. A suite that
exceeds its 300 s budget blocks rather than failing open. COMMIT_RE also
matches `git commit` inside quoted text (e.g. echo "git commit"); that only
runs the suite needlessly, so the fail-closed false positive is accepted.

Interpreter (2026-07-27): the suite is run on a resolved Python >= 3.11, not on
`sys.executable`. The hook inherits the agent process's `python3`, and when that
was 3.9 every module died on `import tomllib` — a green suite reported RED and
no commit could land. "Cannot run the suite" is now its own blocked-with-reason
message, because a gate that reports the wrong failure sends people to fix the
wrong thing.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

COMMIT_RE = re.compile(r"\bgit\b[^|;&\n]*\bcommit\b")
# Shell quote concatenation splits a keyword without changing what runs:
# `git com''mit` and `git com""mit` both execute a real commit, but neither the
# settings prefilter nor COMMIT_RE sees the word. Matching a quote-stripped
# copy in addition to the raw command closes that (reproduced 2026-07-28).
# Stripping can only reveal more matches, never hide one, so detection is
# monotonic. False positives (`echo "git" "commit"`) only run the suite
# needlessly, which the module already accepts.
QUOTE_RE = re.compile(r"[\"'\\]")
# Expansions do the same thing one layer later: the text `g${E}it com${E}mit`
# is not a commit, the process it starts is (reproduced 2026-07-29). Deleting
# the spans reads them as the empty string, which is what evasion uses them
# for; a spelling where the expansion produces the real word is still caught by
# the raw copy, since every copy is matched.
EXPANSION_RE = re.compile(
    r"\$\((?:[^()]|\([^()]*\))*\)"   # $( ... ), one level of nesting
    r"|`[^`]*`"                      # legacy backtick substitution
    r"|\$\{[^}]*\}"                  # ${VAR}, ${VAR:-default}
    r"|\$[A-Za-z_][A-Za-z0-9_]*"     # $VAR
)
# Marks where an expansion stood, for the structural check below. It has to be
# a character no command line contains, so it cannot be typed into place.
EXPANDED = "\x00"
GIT_RE = re.compile(r"\bgit\b([^|;&\n]*)")
# `git -C <path>`, `git -c k=v` and friends take a value; git's remaining own
# options do not, so the first token that is neither is the subcommand.
GIT_VALUE_OPTIONS = ("-C", "-c", "--git-dir", "--work-tree", "--namespace")
# The suite needs stdlib tomllib, so it cannot run below 3.11. Newest first;
# `python3-run` in the .agents layer keeps the same ladder, but a fail-closed
# gate must not depend on another layer being synced.
MIN_PYTHON = (3, 11)
INTERPRETERS = ("python3.14", "python3.13", "python3.12", "python3.11", "python3")
# The escape hatch must be a real leading shell assignment. A bare substring
# match let the token anywhere — e.g. inside a commit message — disarm the gate.
SKIP_RE = re.compile(r"^\s*(?:env\s+)?AGENT_SKIP_TEST_GATE=1(?=\s)")
DASH_C_RE = re.compile(r"\bgit\s+(?:[^|;&\n]*?\s)?-C[= ]\s*(\"[^\"]+\"|'[^']+'|\S+)")
CD_RE = re.compile(r"\bcd\s+(\"[^\"]+\"|'[^']+'|\S+)")
# Shell separators. Assignments and command position are per-segment notions:
# `R=/repo; git -C $R commit` is two commands, and only the first token of the
# second one is the executable.
SEGMENT_RE = re.compile(r"[;&|\n]+")
# A leading `NAME=value` in a segment. Anchored and applied from the segment
# start outward, so `git commit -m "R=/etc"` cannot define R.
ASSIGN_RE = re.compile(r"\s*([A-Za-z_][A-Za-z0-9_]*)=(\"[^\"]*\"|'[^']*'|\S*)")
KNOWN_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")
# Whether a fragment still depends on the shell. Deliberately the characters
# rather than EXPANSION_RE: a fragment cut out of the command by another regex
# can hold half a span (`G=$(echo git)` splits at the space, leaving `$(echo`),
# which no complete-span pattern matches while it is still very much an
# expansion. Wrong-way-round here means calling a literal path unresolved,
# which blocks with a reason; the other way round means allowing a commit.
EXPANSION_CHARS = "$`"


def holds_expansion(text: str) -> bool:
    return any(char in text for char in EXPANSION_CHARS)


def known_values(command: str) -> dict[str, str]:
    """Names whose values this hook can actually see, in shell precedence order.

    Two sources, both real: the hook's own environment (an exported name the
    agent set earlier is right there in `os.environ`) and assignments made by
    the command itself, which win because that is what the shell would do.
    A value that is itself an expansion is skipped rather than half-resolved -
    the structural checks below are the ones meant to decide those.
    """
    values = dict(os.environ)
    for segment in SEGMENT_RE.split(command):
        pos = 0
        while True:
            match = ASSIGN_RE.match(segment, pos)
            if match is None:
                break  # first non-assignment token ends the assignment prefix
            value = match.group(2).strip("\"'")
            if not holds_expansion(value):
                values[match.group(1)] = value
            pos = match.end()
    return values


def expand_known(command: str) -> str:
    """Substitute the expansions whose values are known; leave the rest alone.

    This is the copy that turns `G=git; $G commit` and `git -C "$R" commit`
    back into the literal commands they will become, so ordinary detection and
    ordinary target resolution work on them. Names with no value stay verbatim,
    which keeps them visible to the structural checks instead of silently
    collapsing to the empty string.
    """
    values = known_values(command)

    def replace(match: re.Match[str]) -> str:
        name = match.group(1) or match.group(2)
        return values.get(name, match.group(0))

    return KNOWN_RE.sub(replace, command)


def runtime_subcommand(command: str) -> bool:
    """True if some `git` invocation gets its subcommand from an expansion.

    `C=commit; git $C` deletes down to `git`, which no amount of text matching
    can classify: the word that decides it does not exist until the shell runs.
    Treat only that shape as a possible commit - an expansion standing where
    the subcommand goes - so `git log $(git rev-parse HEAD)`, whose subcommand
    is right there, keeps costing nothing.
    """
    marked = EXPANSION_RE.sub(EXPANDED, QUOTE_RE.sub("", command))
    for rest in GIT_RE.findall(marked):
        if EXPANDED not in rest:
            continue
        tokens = rest.split()
        while tokens and tokens[0].startswith("-"):
            option = tokens.pop(0)
            if option in GIT_VALUE_OPTIONS and tokens:
                tokens.pop(0)
        if not tokens or EXPANDED in tokens[0]:
            return True
    return False


def runtime_executable(command: str) -> bool:
    """True if a segment runs an expansion-produced program on `commit`.

    `G=git; $G commit` with G unreachable leaves no `git` anywhere, so every
    text copy is blind to it - but the shape is still readable: an executable
    that does not exist until run time, invoked with `commit` among its
    arguments. Gate that and nothing else. `echo "git commit" && cd "$HOME"`
    keeps a literal executable in both segments and stays free.
    """
    marked = EXPANSION_RE.sub(EXPANDED, expand_known(QUOTE_RE.sub("", command)))
    for segment in SEGMENT_RE.split(marked):
        tokens = segment.split()
        while tokens and ASSIGN_RE.fullmatch(tokens[0]):
            tokens.pop(0)  # leading assignments are not the command
        if tokens and EXPANDED in tokens[0] and "commit" in tokens[1:]:
            return True
    return False


def resolve_targets(command: str, cwd: str) -> tuple[list[str], list[str]]:
    """Split the repos a command can touch into resolved and unresolved.

    Resolution runs on the expanded copy, so `git -C "$R" commit` and
    `cd "$R" && git commit` name a real directory whenever R's value is in
    reach. Anything still carrying an expansion is returned as unresolved
    rather than passed to `git rev-parse`, where it would fail and quietly
    leave the gate with nothing to check - the caller blocks on those instead.
    """
    expanded = expand_known(command)
    dirs = [cwd]
    unresolved: list[str] = []
    for match in DASH_C_RE.findall(expanded) + CD_RE.findall(expanded):
        target = match.strip("\"'")
        if holds_expansion(target):
            unresolved.append(target)
        elif target not in dirs:
            dirs.append(target)
    return dirs, unresolved


def test_suites(root: Path) -> list[Path]:
    """Return real test suites, ignoring empty directories and stale caches."""
    candidates = (
        root / ".claude" / "tests",
        root / "main" / "claude" / "tests",
    )
    return [
        candidate
        for candidate in candidates
        if candidate.is_dir() and any(candidate.glob("test_*.py"))
    ]


def suite_interpreter() -> str | None:
    """Return a Python >= 3.11 to run the suite with, or None if there is none.

    `sys.executable` is whatever launched the hook — the agent process's PATH
    `python3`. When that predates the suite's floor every module dies on
    `import tomllib` and a green suite is reported RED, which is a false signal,
    not a strict one. Resolve the interpreter the suite needs instead of
    inheriting the hook's own; `AGENT_HARNESS_PYTHON` overrides the search.
    """
    probe = f"import sys; raise SystemExit(0 if sys.version_info >= {MIN_PYTHON} else 1)"
    seen: set[str] = set()
    for candidate in (os.environ.get("AGENT_HARNESS_PYTHON"), sys.executable, *INTERPRETERS):
        if not candidate:
            continue
        resolved = shutil.which(candidate)
        if resolved is None or resolved in seen:
            continue
        seen.add(resolved)
        try:
            probed = subprocess.run(
                [resolved, "-c", probe], capture_output=True, timeout=30,
            )
        except (OSError, subprocess.SubprocessError):
            continue  # unusable candidate: keep looking rather than block
        if probed.returncode == 0:
            return resolved
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # malformed input: never break unrelated tool calls
    command = (payload.get("tool_input") or {}).get("command", "")
    if not isinstance(command, str):
        return 0
    # Fold backslash-newline continuations the way the shell does - by deleting
    # the pair, not by replacing it with a space. `git \<newline>commit` is one
    # command either way, but a substituted space also turns the intra-word
    # split `com\<newline>mit` into `com mit`, which runs a real commit and
    # matches nothing. COMMIT_RE still stops at real `;|&` separators.
    command = re.sub(r"\\\n", "", command)
    unquoted = QUOTE_RE.sub("", command)
    if not (COMMIT_RE.search(command)
            or COMMIT_RE.search(unquoted)
            or COMMIT_RE.search(EXPANSION_RE.sub("", unquoted))
            or COMMIT_RE.search(expand_known(unquoted))
            or runtime_subcommand(command)
            or runtime_executable(command)):
        return 0
    # The escape hatch is matched on the raw command only: it has to be a real
    # leading shell assignment, and normalizing here would make it easier to
    # disarm the gate rather than harder.
    if SKIP_RE.match(command):
        return 0

    cwd = payload.get("cwd") or "."
    candidates, unresolved = resolve_targets(command, str(cwd))
    if unresolved:
        # The command commits somewhere this hook cannot name. Running the
        # suites it *can* see would report a green that covers a different
        # repository, so this blocks with the reason instead.
        sys.stderr.write(
            "commit-test-gate: commit target "
            f"{', '.join(unresolved)} could not be resolved - commit blocked.\n"
            "This is not a red suite: the path only exists once the shell expands it, "
            "so no suite could be selected to run.\n"
            "Re-run with the literal path (or prefix with AGENT_SKIP_TEST_GATE=1).\n"
        )
        return 2
    gated_suites: list[tuple[Path, Path]] = []
    for candidate in candidates:
        top = subprocess.run(
            ["git", "-C", candidate, "rev-parse", "--show-toplevel"],
            capture_output=True, text=True,
        )
        if top.returncode != 0:
            continue  # not a git repo (or bad path); let git produce its own error
        root = Path(top.stdout.strip())
        for tests_dir in test_suites(root):
            entry = (root, tests_dir)
            if entry not in gated_suites:
                gated_suites.append(entry)

    if not gated_suites:
        return 0

    interpreter = suite_interpreter()
    if interpreter is None:
        sys.stderr.write(
            "commit-test-gate: no Python >= "
            f"{'.'.join(str(part) for part in MIN_PYTHON)} available - commit blocked.\n"
            "This is not a red suite: the suite needs stdlib tomllib, and an older "
            "interpreter turns every module into an import error.\n"
            "Install a newer Python, put it on PATH, or set AGENT_HARNESS_PYTHON to one "
            "(or prefix with AGENT_SKIP_TEST_GATE=1) and retry.\n"
        )
        return 2

    with tempfile.TemporaryDirectory(prefix="commit-test-gate-") as shim_dir:
        # Picking the interpreter for `unittest` only fixes the top frame. Tests
        # that spawn `#!/usr/bin/env python3` scripts resolve through PATH and
        # would still land on the agent's old python, so the suite would stay
        # half-upgraded and still report false failures. Front PATH with a
        # `python3` shim pointing at the same interpreter.
        env = dict(os.environ)
        env["AGENT_HARNESS_PYTHON"] = interpreter
        shim = Path(shim_dir) / "python3"
        try:
            shim.symlink_to(interpreter)
            front = shim_dir
        except OSError:
            front = str(Path(interpreter).parent)  # best effort; never fatal
        env["PATH"] = os.pathsep.join([front, env.get("PATH", "")])

        for root, tests_dir in gated_suites:
            try:
                result = subprocess.run(
                    [interpreter, "-m", "unittest", "discover",
                     "-s", str(tests_dir), "-p", "test_*.py"],
                    capture_output=True, text=True, timeout=300, env=env,
                )
            except subprocess.TimeoutExpired:
                sys.stderr.write(
                    f"commit-test-gate: suite {tests_dir} exceeded 300s - commit blocked.\n"
                    "Investigate the hang (or prefix with AGENT_SKIP_TEST_GATE=1) and retry.\n"
                )
                return 2
            if result.returncode == 0:
                continue
            tail = "\n".join(result.stderr.strip().splitlines()[-15:])
            sys.stderr.write(
                f"commit-test-gate: test suite {tests_dir} is RED - commit blocked.\n"
                f"{tail}\n"
                "Fix the failures (or prefix with AGENT_SKIP_TEST_GATE=1 to commit a "
                "deliberately red state) and retry.\n"
            )
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
