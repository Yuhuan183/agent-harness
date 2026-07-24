#!/usr/bin/env python3
"""PreToolUse[Bash] gate: a git commit only proceeds on a green test suite.

Motivation (2026-07-23): three times in one session a red suite was committed
because `unittest | tail` swallowed the exit code and `;` broke the chain.
Reminders did not fix it; this hook makes green-before-commit deterministic.

Scope: fires when the Bash command contains a `git commit` and any repository
the command can plausibly target carries test modules under `.claude/tests/`
or the harness bundle's canonical `main/.claude/tests/`. The target set is the
payload `cwd` plus every `git -C <path>` and `cd <path>` operand in the command,
so repo-switching forms cannot dodge the gate. Other repos and non-commit
commands pass through untouched. Escape hatch for intentional red commits
(e.g. committing a failing reproduction): prefix the command with
`AGENT_SKIP_TEST_GATE=1 `.

Exit 0 = allow; exit 2 = block, stderr goes back to the model. A suite that
exceeds its 300 s budget blocks rather than failing open.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

COMMIT_RE = re.compile(r"\bgit\b[^|;&\n]*\bcommit\b")
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
        root / "main" / ".claude" / "tests",
    )
    return [
        candidate
        for candidate in candidates
        if candidate.is_dir() and any(candidate.glob("test_*.py"))
    ]


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # malformed input: never break unrelated tool calls
    command = (payload.get("tool_input") or {}).get("command", "")
    if not isinstance(command, str) or not COMMIT_RE.search(command):
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

    for root, tests_dir in gated_suites:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "unittest", "discover",
                 "-s", str(tests_dir), "-p", "test_*.py"],
                capture_output=True, text=True, timeout=300,
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
