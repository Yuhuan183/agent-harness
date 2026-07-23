#!/usr/bin/env python3
"""PreToolUse[Bash] gate: a git commit only proceeds on a green test suite.

Motivation (2026-07-23): three times in one session a red suite was committed
because `unittest | tail` swallowed the exit code and `;` broke the chain.
Reminders did not fix it; this hook makes green-before-commit deterministic.

Scope: fires only when the Bash command contains a `git commit` and the
repository being committed has a `.claude/tests/` directory. Other repos and
non-commit commands pass through untouched. Escape hatch for intentional
red commits (e.g. committing a failing reproduction): prefix the command
with `AGENT_SKIP_TEST_GATE=1 `.

Exit 0 = allow; exit 2 = block, stderr goes back to the model.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

COMMIT_RE = re.compile(r"\bgit\b[^|;&\n]*\bcommit\b")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # malformed input: never break unrelated tool calls
    command = (payload.get("tool_input") or {}).get("command", "")
    if not isinstance(command, str) or not COMMIT_RE.search(command):
        return 0
    if "AGENT_SKIP_TEST_GATE=1" in command:
        return 0

    cwd = payload.get("cwd") or "."
    top = subprocess.run(
        ["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
        capture_output=True, text=True,
    )
    if top.returncode != 0:
        return 0  # not a git repo; let git produce its own error
    tests_dir = Path(top.stdout.strip()) / ".claude" / "tests"
    if not tests_dir.is_dir():
        return 0

    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", str(tests_dir), "-p", "test_*.py"],
        capture_output=True, text=True, timeout=300,
    )
    if result.returncode == 0:
        return 0
    tail = "\n".join(result.stderr.strip().splitlines()[-15:])
    sys.stderr.write(
        "commit-test-gate: test suite is RED - commit blocked.\n"
        f"{tail}\n"
        "Fix the failures (or prefix with AGENT_SKIP_TEST_GATE=1 to commit a "
        "deliberately red state) and retry.\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
