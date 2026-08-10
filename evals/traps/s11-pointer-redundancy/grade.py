#!/usr/bin/env python3
"""Mechanical answer sheet for s11: did the skill load, and did the run count?

Reads the `--output-format stream-json` event log of one run and the scenario it
was run against. It looks only at emitted events: a `Skill` tool call is a fact
in the stream, whereas the agent saying "I consulted baton-dispatch" is a claim,
and this repo's graders do not grade claims.

Three outcomes, deliberately distinct:

    exit 0  valid and correct   - marker present, load matched the expectation
    exit 1  valid and incorrect - marker present, load did not match
    exit 2  invalid             - marker absent; the run never reached the
                                  branch under test, so it is neither

The third is the one that matters for honesty. A run that wandered off is not
evidence against the clause, and folding it into the failures would let a badly
designed scenario look like a finding. Invalid runs are recorded and counted -
their rate says the scenario is broken, not that the harness is.

Usage:
    grade.py --events run.jsonl --scenario scenarios/b1-parallel-batch.md
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def scenario_spec(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER.search(text)
    if not match:
        raise SystemExit(f"{path}: no frontmatter; a scenario without a declared "
                         "target and marker cannot be graded")
    spec = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            spec[key.strip()] = value.strip()
    for required in ("target", "expect", "marker_pattern"):
        if required not in spec:
            raise SystemExit(f"{path}: frontmatter is missing {required}")
    if spec["expect"] not in ("invoked", "not-invoked"):
        raise SystemExit(f"{path}: expect must be invoked or not-invoked")
    return spec


def read_events(path: Path) -> list[dict]:
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def skills_invoked(events: list[dict]) -> list[str]:
    """Every skill this run actually loaded, by name, from tool-call events."""
    names = []
    for event in events:
        message = event.get("message")
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict) or part.get("type") != "tool_use":
                continue
            if str(part.get("name", "")).lower() not in ("skill", "skilltool"):
                continue
            payload = part.get("input") or {}
            name = payload.get("skill") or payload.get("name") or ""
            # Plugin skills arrive as `plugin:skill`; the bare name is what the
            # scenario declares, so compare on the last segment.
            names.append(str(name).split(":")[-1])
    return names


def transcript_text(events: list[dict]) -> str:
    chunks = []
    for event in events:
        if isinstance(event.get("result"), str):
            chunks.append(event["result"])
        message = event.get("message")
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if isinstance(content, str):
            chunks.append(content)
        elif isinstance(content, list):
            for part in content:
                if not isinstance(part, dict):
                    continue
                if part.get("type") == "text":
                    chunks.append(str(part.get("text", "")))
                elif part.get("type") == "tool_use":
                    chunks.append(json.dumps(part.get("input") or {},
                                             ensure_ascii=False))
    return "\n".join(chunks)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--scenario", required=True, type=Path)
    args = parser.parse_args()

    spec = scenario_spec(args.scenario)
    events = read_events(args.events)
    loaded = skills_invoked(events)
    reached = bool(re.search(spec["marker_pattern"], transcript_text(events)))
    invoked = spec["target"] in loaded
    correct = invoked == (spec["expect"] == "invoked")

    verdict = {
        "scenario": args.scenario.name,
        "target": spec["target"],
        "expect": spec["expect"],
        "marker_present": reached,
        "skills_invoked": loaded,
        "target_invoked": invoked,
        "verdict": "invalid" if not reached else ("correct" if correct else "incorrect"),
    }
    print(json.dumps(verdict, indent=2, ensure_ascii=False))
    if not reached:
        return 2
    return 0 if correct else 1


if __name__ == "__main__":
    sys.exit(main())
