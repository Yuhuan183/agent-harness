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


def text_record(
    relative: str,
    effective_text: str | None = None,
    *,
    kind: str | None = None,
) -> dict:
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
    if kind is not None:
        record["kind"] = kind
    if effective_data != file_data:
        record["file_bytes"] = len(file_data)
        record["file_sha256"] = sha256(file_data)
    return record


def split_frontmatter(relative: str) -> tuple[str, str]:
    text = read_bytes(relative).decode("utf-8")
    parts = text.split("---", 2)
    if len(parts) != 3:
        raise ValueError(f"{relative}: expected YAML frontmatter")
    return parts[1], parts[2].lstrip("\r\n")


def claude_role(relative: str) -> dict:
    _, body = split_frontmatter(relative)
    return text_record(relative, body)


def codex_role(relative: str) -> dict:
    text = read_bytes(relative).decode("utf-8")
    payload = tomllib.loads(text)
    body = payload.get("developer_instructions")
    if not isinstance(body, str):
        raise ValueError(f"{relative}: missing developer_instructions")
    return text_record(relative, body)


def skill_paths(directory: str) -> list[str]:
    return [
        path.relative_to(ROOT).as_posix()
        for path in sorted((ROOT / directory).glob("*/SKILL.md"))
    ]


def skill_frontmatter_fields(frontmatter: str) -> dict[str, str]:
    """Read the two resident skill fields without adding a YAML dependency."""
    fields: dict[str, str] = {}
    lines = frontmatter.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        key, separator, value = line.partition(":")
        key = key.strip()
        scalar = value.strip()
        if separator and not line[:1].isspace() and key in {"name", "description"}:
            if scalar in {"|", "|-", "|+", ">", ">-", ">+"}:
                block: list[str] = []
                index += 1
                while index < len(lines):
                    continuation = lines[index]
                    if continuation and not continuation[:1].isspace():
                        break
                    block.append(continuation.strip())
                    index += 1
                separator_text = "\n" if scalar.startswith("|") else " "
                fields[key] = separator_text.join(block).strip()
                continue
            fields[key] = scalar.strip("\"'")
        index += 1
    return fields


def skill_parts(relative: str) -> tuple[dict, dict]:
    frontmatter, body = split_frontmatter(relative)
    fields = skill_frontmatter_fields(frontmatter)
    if set(fields) != {"name", "description"}:
        raise ValueError(f"{relative}: expected name and description frontmatter")
    metadata = f"{fields['name']} {fields['description']}"
    return (
        text_record(relative, metadata, kind="skill-metadata"),
        text_record(relative, body, kind="skill-body"),
    )


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
    claude_skills = [
        skill_parts(relative)
        for relative in skill_paths("main/claude/skills")
    ]
    codex_skills = [
        skill_parts(relative)
        for relative in skill_paths("main/codex/skills")
    ]
    providers = {
        "claude": {
            "resident": [
                text_record("main/claude/CLAUDE.contract.md"),
                *(metadata for metadata, _ in claude_skills),
            ],
            "dispatch": [
                *(body for _, body in claude_skills),
            ],
            "roles": [
                claude_role(f"main/claude/agents/{role}.md") for role in ROLES
            ],
        },
        "codex": {
            "resident": [
                text_record("main/codex/AGENTS.contract.md"),
                *(metadata for metadata, _ in codex_skills),
            ],
            "dispatch": [
                *(body for _, body in codex_skills),
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
            "skills": "name and description are resident; body is dispatch-time",
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
