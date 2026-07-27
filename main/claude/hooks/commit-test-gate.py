#!/usr/bin/env python3
"""PreToolUse[Bash] gate: a git commit only proceeds on a green test suite.

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


def candidate_dirs(command: str, cwd: str) -> list[str]:
    dirs = [cwd]
    for match in DASH_C_RE.findall(command) + CD_RE.findall(command):
        dirs.append(match.strip("\"'"))
    return dirs


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
    # Fold backslash-newline continuations: `git \<newline>commit` is one
    # command, but the raw newline would otherwise split `git` from `commit`
    # and slip the gate. COMMIT_RE still stops at real `;|&` separators.
    command = re.sub(r"\\\n", " ", command)
    if not COMMIT_RE.search(command):
        return 0
    if SKIP_RE.match(command):
        return 0

    cwd = payload.get("cwd") or "."
    gated_suites: list[tuple[Path, Path]] = []
    for candidate in candidate_dirs(command, str(cwd)):
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
