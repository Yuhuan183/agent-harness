#!/usr/bin/env python3
"""Census of the Codex host prompt, per session kind, from local rollouts.

Companion to `prompt-surface-census.py`: that one measures the prompt surface
*we* ship, this one measures the one the vendor ships, because several clauses
in `main/codex/AGENTS.contract.md` are kept or dropped on the strength of what
Codex already says.

Codex records its host prompt in `session_meta.base_instructions` of every
rollout under `~/.codex/sessions` (override: `CODEX_SESSIONS_DIR`), so the
evidence is provider-recorded rather than inferred. Claude Code has no
equivalent - it records its system prompt nowhere - so the same audit cannot
be run on that side at all.

Why this exists as a script rather than a paragraph: the 2026-07-31 audit was
run twice by hand and got the wrong answer the first time, by reading one
rollout out of ninety-one. There are eight distinct host prompts in that set,
and the deciding axis is session kind, not CLI version - a top-level session
and a subagent get materially different prompts, while both are handed
`AGENTS.contract.md` as instructions. A one-off analysis that cannot be re-run
gets re-derived, and re-derived wrongly.

This deliberately has no `--check` mode. The snapshot it reports is
machine-local and expected to move; pinning it would produce a check that
fails for every user who is not the author. Its output is evidence for a human
decision, not a gate.

    scripts/codex-prompt-census.py                  # table
    scripts/codex-prompt-census.py --min-cli 0.145  # current generation only
    scripts/codex-prompt-census.py --json
"""
from __future__ import annotations

import argparse
import collections
import glob
import hashlib
import json
import os
import re
import sys

SESSIONS = os.environ.get(
    "CODEX_SESSIONS_DIR", os.path.expanduser("~/.codex/sessions"))

# Each entry pairs a clause of `main/codex/AGENTS.contract.md` with the vendor
# text that would make it a restatement. `main/claude/tests/test_contracts.py`
# justifies its keep/drop decisions from these same clauses, and
# `test_the_vendor_census_covers_every_justified_clause` fails if the two lists
# stop matching - the tool and the reasoning have to move together.
CONTRACT_CLAUSES = (
    ("dirty-worktree", "preserve dirty worktrees and unrelated user work",
     "you preserve them, ignore unrelated edits"),
    ("no-ask-scoped", "need no approval",
     "You do not need to ask for clarification"),
    ("autonomy", "inspect and report",
     "## Autonomy and persistence"),
    ("authority", "require explicit authority",
     "# Destructive Actions"),
)

# The evidence channel is only usable if it carries the vendor's words and not
# ours. A rollout for work in this repo has our contract all over its tool
# output; `base_instructions` must stay clean of it or the audit is circular.
OUR_MARKERS = (
    "Global Working Contract", "leaf-dispatch", "LEAF_DISPATCH",
    "Traditional Chinese", "DECISION:",
)


def cli_tuple(version: str) -> tuple[int, ...]:
    """Leading numeric triple; `0.145.0-alpha.18` sorts with `0.145.0`."""
    head = re.split(r"[-+]", str(version))[0]
    parts = []
    for piece in head.split("."):
        try:
            parts.append(int(piece))
        except ValueError:
            break
    return tuple(parts)


def sessions() -> list[dict]:
    """One record per rollout that carries a host prompt."""
    found = []
    for path in sorted(glob.glob(os.path.join(SESSIONS, "*/*/*/rollout-*.jsonl"))):
        try:
            with open(path, encoding="utf-8", errors="replace") as stream:
                for line in stream:
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(record, dict):
                        continue
                    if record.get("type") != "session_meta":
                        continue
                    payload = record.get("payload")
                    if not isinstance(payload, dict):
                        break
                    base = payload.get("base_instructions")
                    text = base.get("text") if isinstance(base, dict) else None
                    if not isinstance(text, str) or not text:
                        break
                    source = str(payload.get("source"))
                    found.append({
                        "path": os.path.basename(path),
                        "text": text,
                        "sha": hashlib.sha256(text.encode("utf-8")).hexdigest()[:12],
                        "chars": len(text),
                        "cli": str(payload.get("cli_version")),
                        # Codex hands a subagent a different, thinner prompt.
                        # This is the axis the first audit missed.
                        "kind": "subagent" if "subagent" in source else "top-level",
                        "date": str(payload.get("timestamp"))[:10],
                    })
                    break
        except OSError:
            continue
    return found


def census(min_cli: str | None = None) -> dict:
    rows = sessions()
    if min_cli:
        floor = cli_tuple(min_cli)
        rows = [r for r in rows if cli_tuple(r["cli"])[:len(floor)] >= floor]
    by_kind: dict[str, collections.Counter] = collections.defaultdict(
        collections.Counter)
    for row in rows:
        by_kind[row["kind"]]["n"] += 1
        for label, _clause, needle in CONTRACT_CLAUSES:
            if needle in row["text"]:
                by_kind[row["kind"]][label] += 1
    variants = collections.Counter(r["sha"] for r in rows)
    leaked = sorted({m for r in rows for m in OUR_MARKERS if m in r["text"]})
    return {
        "sessions_dir": SESSIONS,
        "rollouts_with_host_prompt": len(rows),
        "distinct_prompts": len(variants),
        "min_cli": min_cli,
        "coverage": {
            kind: {"n": counter["n"],
                   **{label: counter[label] for label, _, _ in CONTRACT_CLAUSES}}
            for kind, counter in by_kind.items()
        },
        "our_markers_leaked_into_host_prompt": leaked,
    }


def render(result: dict) -> str:
    lines = [
        f"codex host-prompt census — {result['rollouts_with_host_prompt']} rollouts, "
        f"{result['distinct_prompts']} distinct prompts"
        + (f", cli >= {result['min_cli']}" if result["min_cli"] else ""),
        "",
    ]
    if not result["coverage"]:
        lines.append("  no rollouts found under " + result["sessions_dir"])
        return "\n".join(lines)
    width = max(len(label) for label, _, _ in CONTRACT_CLAUSES) + 4
    lines.append(f"{'session kind':14}{'n':>5}  "
                 + "".join(f"{label:>{width}}" for label, _, _ in CONTRACT_CLAUSES))
    for kind, counts in sorted(result["coverage"].items()):
        n = counts["n"]
        lines.append(f"{kind:14}{n:>5}  " + "".join(
            f"{f'{counts[label]}/{n}':>{width}}" for label, _, _ in CONTRACT_CLAUSES))
    lines += ["", "Each column is the vendor text that would make one contract "
              "clause a restatement:"]
    for label, clause, needle in CONTRACT_CLAUSES:
        lines.append(f"  {label:<16}{clause!r} <- {needle!r}")
    lines += [
        "",
        "A clause the thinnest consumer's prompt does not carry must stay in",
        "the contract, whatever a richer variant says. Both kinds are handed",
        "AGENTS.contract.md as instructions, so subagent is the floor.",
    ]
    if result["our_markers_leaked_into_host_prompt"]:
        lines += ["", "WARNING: our own contract text appears in the host prompt "
                  f"({', '.join(result['our_markers_leaked_into_host_prompt'])}); "
                  "this evidence channel is circular and cannot justify a deletion"]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="machine-readable")
    parser.add_argument("--min-cli", metavar="VERSION",
                        help="only rollouts at or above this CLI version")
    args = parser.parse_args()
    result = census(args.min_cli)
    print(json.dumps(result, indent=2, sort_keys=True) if args.json
          else render(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
