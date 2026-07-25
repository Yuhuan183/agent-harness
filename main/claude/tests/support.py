"""Shared fixtures and helpers for the contract test suite."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
import unittest
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
BASH_ROLES = (
    "mech-executor",
    "executor",
    "verifier",
    "security-executor",
)
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
