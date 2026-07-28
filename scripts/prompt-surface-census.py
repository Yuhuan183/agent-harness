#!/usr/bin/env python3
"""Emit a deterministic census of resident, dispatch, and role prompt surfaces."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROLES = (
    "explore",
    "plan-verifier",
    "security-reviewer",
    "mech-executor",
    "executor",
    "verifier",
    "security-executor",
)


def word_count(text: str) -> int:
    """Use the repository's CJK-aware resident-attention budget unit."""
    return len(re.findall(r"[\u4e00-\u9fff]|[^\s\u4e00-\u9fff]+", text))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_bytes(relative: str) -> bytes:
    return (ROOT / relative).read_bytes()


def text_record(relative: str, effective_text: str | None = None) -> dict:
    file_data = read_bytes(relative)
    text = file_data.decode("utf-8")
    effective = text if effective_text is None else effective_text
    effective_data = effective.encode("utf-8")
    record = {
        "path": relative,
        "bytes": len(effective_data),
        "sha256": sha256(effective_data),
        "words": word_count(effective),
    }
    if effective_data != file_data:
        record["file_bytes"] = len(file_data)
        record["file_sha256"] = sha256(file_data)
    return record


def claude_role(relative: str) -> dict:
    text = read_bytes(relative).decode("utf-8")
    parts = text.split("---", 2)
    if len(parts) != 3:
        raise ValueError(f"{relative}: expected YAML frontmatter")
    return text_record(relative, parts[2].lstrip("\r\n"))


def codex_role(relative: str) -> dict:
    text = read_bytes(relative).decode("utf-8")
    payload = tomllib.loads(text)
    body = payload.get("developer_instructions")
    if not isinstance(body, str):
        raise ValueError(f"{relative}: missing developer_instructions")
    return text_record(relative, body)


def layer_total(records: list[dict]) -> dict:
    binding = hashlib.sha256()
    for record in records:
        binding.update(record["path"].encode("utf-8"))
        binding.update(b"\0")
        binding.update(record["sha256"].encode("ascii"))
        binding.update(b"\0")
    return {
        "bytes": sum(record["bytes"] for record in records),
        "words": sum(record["words"] for record in records),
        "payload_sha256": binding.hexdigest(),
    }


def build_census() -> dict:
    providers = {
        "claude": {
            "resident": [
                text_record("main/claude/CLAUDE.contract.md"),
            ],
            "dispatch": [
                text_record("main/claude/skills/baton-dispatch/SKILL.md"),
                text_record("main/claude/skills/provider-routing/SKILL.md"),
            ],
            "roles": [
                claude_role(f"main/claude/agents/{role}.md") for role in ROLES
            ],
        },
        "codex": {
            "resident": [
                text_record("main/codex/AGENTS.contract.md"),
            ],
            "dispatch": [
                text_record("main/codex/skills/leaf-dispatch/SKILL.md"),
            ],
            "roles": [
                codex_role(f"main/codex/agents/{role}.toml") for role in ROLES
            ],
        },
    }
    totals = {
        provider: {
            layer: layer_total(records)
            for layer, records in layers.items()
        }
        for provider, layers in providers.items()
    }
    return {
        "schema": 1,
        "generated_by": "scripts/prompt-surface-census.py",
        "unit": {
            "bytes": "UTF-8 bytes of the effective prompt text",
            "words": "one CJK character or one non-space non-CJK run",
            "roles": "role body only; file_bytes/file_sha256 bind frontmatter or TOML",
        },
        "providers": providers,
        "totals": totals,
    }


def render() -> bytes:
    return (json.dumps(
        build_census(), ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n").encode("utf-8")


def resolve_output(path: str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else ROOT / candidate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", metavar="PATH")
    mode.add_argument("--check", metavar="PATH")
    args = parser.parse_args()
    output = render()

    if args.write:
        target = resolve_output(args.write)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(output)
        return 0
    if args.check:
        target = resolve_output(args.check)
        if not target.exists() or target.read_bytes() != output:
            print(
                f"stale prompt census: {target}\n"
                f"refresh with: main/.agents/scripts/python3-run "
                f"scripts/prompt-surface-census.py --write {args.check}",
                file=sys.stderr,
            )
            return 1
        return 0

    sys.stdout.buffer.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
