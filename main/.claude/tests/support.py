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
    source = Path(path)
    if source.parts and source.parts[0] in {".claude", ".codex", ".agents"}:
        source = Path("main") / source
    return (ROOT / source).read_text(encoding="utf-8")


def deployment_manifest() -> list[tuple[str, str]]:
    pairs = []
    for raw in read("scripts/deployment-manifest.tsv").splitlines():
        if not raw or raw.startswith("#"):
            continue
        source, target = raw.split("\t")
        pairs.append((source, target))
    return pairs


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
