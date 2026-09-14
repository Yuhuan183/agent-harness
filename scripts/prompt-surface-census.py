#!/usr/bin/env python3
# Read: every change to a contract, role or skill description (`--write` is the required step, not this reading)
"""Emit a deterministic census of resident, dispatch, and role prompt surfaces.

Why this exists. The Context layer prices a clause per turn, and pricing needs
a number that does not move when nobody changed anything - so this emits the
same bytes for the same tree, and `docs/research/prompt-surface-census.json` is
that snapshot. `test_contracts.py` compares against it with `--check`, which is
what turns "the resident surface grew" from something a person might notice
into something a commit cannot pass without answering for.

What it measures is deliberately wider than the contracts. The resident bucket
holds both contract bodies *plus* every skill's and role's `name` and
`description`, because those are injected every turn as well; counting role
bodies alone left half the resident cost outside the budget until 2026-08-01,
and that half was also the ratchet's only bypass - move a sentence from a skill
description into a role description and the cost is unchanged while the tests
stay green.

What it does not measure is the other five sixths. Skills installed on the
machine but not shipped by this repo are in the same injected block and are not
counted here; `resident-pool-report.py` is the view that includes them, and
`docs/architecture/context-engineering.md` says why that one reports rather
than gates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
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
    path: str | None = None,
) -> dict:
    file_data = read_bytes(relative)
    text = file_data.decode("utf-8")
    effective = text if effective_text is None else effective_text
    effective_data = effective.encode("utf-8")
    record = {
        "path": path or relative,
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


# A role's body is dispatch-time cost, paid only when that role runs. Its name
# and description are not: the CLI lists every registered role in every session
# as the agent-selection surface, exactly the way a skill's name and description
# are listed. Counting only the body left the always-loaded half of a role
# outside the census and outside every budget, so a clause moved from a skill
# description into a role description cost the same and measured as nothing
# (2026-08-01 review).


def claude_role_metadata(relative: str) -> dict:
    frontmatter, _ = split_frontmatter(relative)
    fields = skill_frontmatter_fields(frontmatter)
    missing = {"name", "description"} - set(fields)
    if missing:
        raise ValueError(f"{relative}: frontmatter missing {sorted(missing)}")
    metadata = f"{fields['name']} {fields['description']}"
    return text_record(relative, metadata, kind="role-metadata")


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
    providers = {
        "claude": {
            "resident": [
                text_record("main/claude/CLAUDE.contract.md"),
                *(metadata for metadata, _ in claude_skills),
                *(claude_role_metadata(f"main/claude/agents/{role}.md")
                  for role in ROLES),
            ],
            "dispatch": [
                *(body for _, body in claude_skills),
            ],
            "roles": [
                claude_role(f"main/claude/agents/{role}.md") for role in ROLES
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
            "skills": "name and description are resident, body is dispatch-time",
            "bytes": "UTF-8 bytes of the effective prompt text",
            "words": "one CJK character or one non-space non-CJK run",
            "roles": "role body only; the always-loaded name and description are counted in resident as role-metadata",
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
