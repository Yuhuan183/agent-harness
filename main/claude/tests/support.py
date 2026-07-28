"""Shared fixtures and helpers for the contract test suite."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile

# Fail with the actual cause before `import tomllib` fails with a misleading
# one. Below 3.11 every module in this suite dies on that import, and unittest
# reports it as an error in each test file — a wall of red that reads like the
# harness is broken. It happened for real: /usr/bin/python3 is 3.9 on macOS, so
# any agent or hook that inherits the system PATH lands here. commit-test-gate
# resolves an interpreter for exactly this reason; the suite should say the
# same thing when it is run by hand.
if sys.version_info < (3, 11):
    raise SystemExit(
        f"agent-harness tests need Python >= 3.11 for stdlib tomllib; this is "
        f"{sys.version.split()[0]} at {sys.executable}. Run the suite with a "
        f"newer interpreter (and put it on PATH — subprocess-spawned scripts "
        f"resolve `python3` themselves)."
    )

import tomllib  # noqa: E402  (guarded above; the guard must run first)
import unittest  # noqa: E402
from datetime import datetime, timedelta, timezone
from pathlib import Path


# Repo root: deployable harness sources live under main/; docs and evals stay
# at the project root.
ROOT = Path(__file__).resolve().parents[3]

ROLES = (
    "explore",
    "plan-verifier",
    "security-reviewer",
    "mech-executor",
    "executor",
    "verifier",
    "security-executor",
)
# Role spelling is lowercase on both providers since the 2026-07-23 rename.
CODEX_ROLES = ROLES
READ_ONLY_ROLES = (
    "explore",
    "plan-verifier",
    "security-reviewer",
)
# `verifier` holds Bash because its contract forbids believing a test report it
# has not reproduced, and Claude Code cannot grant a partial Bash: the boundary
# is drawn by hooks/readonly-bash.py instead. It is a read-only role with a
# guarded tool, not a writer — grouping it with the writers is what let it
# claim a sandbox it did not have.
GUARDED_BASH_ROLES = ("verifier",)
# The tools a guarded read-only role may hold. Asserted as an upper bound, not
# as a list of forbidden names: enumerating what must be absent (Write, Edit,
# Agent, ...) rebuilds in the test the denylist the frontmatter allowlist
# exists to avoid, and anything nobody thought to enumerate - a new mutating
# built-in, an MCP tool - would be granted silently.
GUARDED_BASH_TOOLS = frozenset(
    {"Read", "Glob", "Grep", "Bash", "WebSearch", "WebFetch"}
)
WRITER_ROLES = (
    "mech-executor",
    "executor",
    "security-executor",
)
BASH_ROLES = GUARDED_BASH_ROLES + WRITER_ROLES
# Roles that must not be able to mutate the repository, whatever tools they hold.
# Mirrors the Codex twins' enforced sandbox_mode = "read-only".
NO_WRITE_ROLES = READ_ONLY_ROLES + GUARDED_BASH_ROLES
# Role bodies are budgeted in words on both providers. `executor` is the
# largest at 378 (2026-07-26); raise this deliberately with a reason, the way
# the contract budgets are raised, rather than by lengthening lines.
ROLE_BODY_BUDGET = 400
# Every role pins model and effort from the active deployment preset (user-directed
# 2026-07-22); no role follows the main-session effort.
PINNED_EFFORT_ROLES = ROLES
FOLLOW_EFFORT_ROLES = ()

# Interface tokens: single upgrade point — bump here and in the skill bodies together.
CODEX_BRIDGE = "codex:codex-rescue"
DISPATCH_OPTIONS = ("Dispatch GPT + Claude", "Dispatch GPT", "Dispatch Claude")


def read(path: str) -> str:
    """Accepts the deployed (HOME-relative) path and resolves it to the source.

    Claude Code and Codex discover config from `.claude/` and `.codex/` below
    the working directory, so a source tree named that way competes with the
    deployed copy it exists to produce. Those two drop the dot in the repo and
    regain it from the manifest's target column at deploy time.

    `.agents/` keeps its dot. Nothing discovers it — it is this project's own
    convention rather than a standard — and both bundles reach the shared skills
    through relative symlinks (`../../.agents/skills/<name>`) that rsync copies
    verbatim. Those links must therefore resolve identically in the repo and in
    `$HOME`; renaming the shared root here would deploy 13 broken links.
    """
    source = Path(path)
    if source.parts and source.parts[0] in {".claude", ".codex"}:
        source = Path("main") / source.parts[0].lstrip(".") / Path(*source.parts[1:])
    elif source.parts and source.parts[0] == ".agents":
        source = Path("main") / source
    return (ROOT / source).read_text(encoding="utf-8")


def deployment_manifest() -> list[tuple[str, str]]:
    return [(source, target) for source, target, _ in deployment_manifest_entries()]


def deployment_manifest_entries() -> list[tuple[str, str, str]]:
    entries = []
    for raw in read("scripts/deployment-manifest.tsv").splitlines():
        if not raw or raw.startswith("#"):
            continue
        fields = raw.split("\t")
        source, target = fields[:2]
        mode = fields[2] if len(fields) == 3 else ""
        entries.append((source, target, mode))
    return entries


def frontmatter(path: str) -> str:
    return read(path).split("---", 2)[1]


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True,
        text=True,
    )


def word_count(text: str) -> int:
    """Budget unit: each CJK character counts as one word; other runs of
    non-space text count as one. Plain split() would let Chinese prose dodge
    the resident-attention budget entirely."""
    return len(re.findall(r"[\u4e00-\u9fff]|[^\s\u4e00-\u9fff]+", text))
