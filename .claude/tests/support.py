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


# Repo root: the tracked harness spans .claude/, .codex/, .agents/, and docs/.
ROOT = Path(__file__).resolve().parents[2]

ROLES = (
    "Explore",
    "plan-verifier",
    "security-reviewer",
    "mech-executor",
    "executor",
    "verifier",
    "security-executor",
)
CODEX_ROLES = tuple(role.lower() if role == "Explore" else role for role in ROLES)
READ_ONLY_ROLES = (
    "Explore",
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
    return (ROOT / path).read_text(encoding="utf-8")


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


