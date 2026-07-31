#!/usr/bin/env python3
"""Census of the Codex host prompt, per session kind, from local rollouts.

Companion to `prompt-surface-census.py`: that one measures the prompt surface
*we* ship, this one measures the one the vendor ships, because several clauses
in `main/codex/AGENTS.contract.md` are kept or dropped on the strength of what
Codex already says.

Codex records its host prompt in `session_meta.base_instructions` of every
rollout under its home directory (`~/.codex`; override: `CODEX_SESSIONS_DIR`),
so the evidence is provider-recorded rather than inferred. Claude Code has no
equivalent - it records its system prompt nowhere - so the same audit cannot
be run on that side at all.

Why this exists as a script rather than a paragraph: the 2026-07-31 audit was
run by hand and got the wrong answer, by reading one rollout out of hundreds.
There are several distinct host prompts in that set, and the deciding axis is
session kind, not CLI version - a top-level session and a subagent get
materially different prompts, while both are handed `AGENTS.contract.md` as
instructions. An analysis that cannot be re-run gets re-derived, and
re-derived wrongly.

**The denominator is the whole point.** A tool that answers "is this clause
already guaranteed?" is only safe if it can say what it failed to look at: an
unreadable rollout, a format it does not understand, or an entire store it
never globbed all shrink the sample silently, and a smaller sample makes vendor
coverage look *more* complete than it is - the direction that licenses a
deletion that should not happen. Both of those have happened here: the first
version globbed only `sessions/` and missed `archived_sessions/` entirely, and
it dropped unparseable rollouts without a word. So this reports
discovered/usable/skipped, and refuses to certify an incomplete sample.

There is deliberately no `--check` against a pinned snapshot: the input is
machine-local and expected to move, so pinning it would fail for every user who
is not the author. The non-zero exit means "this sample cannot support a
deletion decision", not "the numbers changed".

    scripts/codex-prompt-census.py                  # table
    scripts/codex-prompt-census.py --min-cli 0.145  # current generation only
    scripts/codex-prompt-census.py --json
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import re
import sys
from pathlib import Path

# The rollout store root. Both `sessions/` (nested by date) and
# `archived_sessions/` (flat) live under it, and archiving is a user action,
# not a staleness marker - the two hold the same population, so discovery is
# rooted at the home and recursive rather than at one store with a fixed depth.
CODEX_HOME = Path(os.environ.get(
    "CODEX_SESSIONS_DIR", os.path.expanduser("~/.codex")))

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

SKIP_REASONS = {
    "unreadable": "file could not be read",
    "no_session_meta": "no session_meta record",
    "unsupported_base_instructions": "session_meta carried no readable host "
                                     "prompt (format drift?)",
}


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


def host_prompt(payload: dict) -> str | None:
    """The host prompt text, or None if this payload does not carry one.

    Every local rollout spells it `{"text": ...}`. A bare string is accepted
    too, because that shape costs one line to support and a format change that
    silently halves the sample is exactly what this file is defending against.
    Anything else is a skip with a reason, never a silent drop.
    """
    base = payload.get("base_instructions")
    if isinstance(base, dict):
        base = base.get("text")
    return base if isinstance(base, str) and base else None


def scan() -> tuple[list[dict], collections.Counter]:
    """Every discovered rollout, split into usable records and skip reasons."""
    usable: list[dict] = []
    skipped: collections.Counter = collections.Counter()
    for path in sorted(CODEX_HOME.rglob("rollout-*.jsonl")):
        try:
            meta = None
            with open(path, encoding="utf-8", errors="replace") as stream:
                for line in stream:
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(record, dict):
                        continue
                    if record.get("type") == "session_meta":
                        payload = record.get("payload")
                        meta = payload if isinstance(payload, dict) else {}
                        break
        except OSError:
            skipped["unreadable"] += 1
            continue
        if meta is None:
            skipped["no_session_meta"] += 1
            continue
        text = host_prompt(meta)
        if text is None:
            skipped["unsupported_base_instructions"] += 1
            continue
        source = str(meta.get("source"))
        usable.append({
            "path": str(path.relative_to(CODEX_HOME)),
            # Which store it sits in; both are in scope, and the split is
            # reported because the first version only saw one of them.
            "store": path.relative_to(CODEX_HOME).parts[0],
            "text": text,
            "sha": hashlib.sha256(text.encode("utf-8")).hexdigest()[:12],
            "chars": len(text),
            "cli": str(meta.get("cli_version")),
            # Codex hands a subagent a different, thinner prompt. This is the
            # axis the first audit missed, and the thinner one is the floor.
            "kind": "subagent" if "subagent" in source else "top-level",
            "date": str(meta.get("timestamp"))[:10],
        })
    return usable, skipped


def census(min_cli: str | None = None) -> dict:
    usable, skipped = scan()
    parsed = len(usable)
    discovered = parsed + sum(skipped.values())
    if min_cli:
        floor = cli_tuple(min_cli)
        usable = [r for r in usable
                  if cli_tuple(r["cli"])[:len(floor)] >= floor]
    by_kind: dict[str, collections.Counter] = collections.defaultdict(
        collections.Counter)
    for row in usable:
        by_kind[row["kind"]]["n"] += 1
        for label, _clause, needle in CONTRACT_CLAUSES:
            if needle in row["text"]:
                by_kind[row["kind"]][label] += 1
    leaked = sorted({m for r in usable for m in OUR_MARKERS if m in r["text"]})
    # An incomplete or circular sample cannot say a clause is already
    # guaranteed, so it does not get to look like an answer.
    unresolved = []
    if skipped:
        unresolved.append(
            "sample incomplete: " + ", ".join(
                f"{n} {SKIP_REASONS.get(reason, reason)}"
                for reason, n in sorted(skipped.items())))
    if not usable:
        unresolved.append("no usable rollouts")
    if leaked:
        unresolved.append(
            "circular evidence: our own contract text appears in the host "
            "prompt (" + ", ".join(leaked) + ")")
    return {
        "codex_home": str(CODEX_HOME),
        "discovered": discovered,
        "parsed": parsed,
        "usable": len(usable),
        "skipped": dict(skipped),
        "stores": dict(collections.Counter(r["store"] for r in usable)),
        "distinct_prompts": len({r["sha"] for r in usable}),
        "min_cli": min_cli,
        "coverage": {
            kind: {"n": counter["n"],
                   **{label: counter[label] for label, _, _ in CONTRACT_CLAUSES}}
            for kind, counter in by_kind.items()
        },
        "our_markers_leaked_into_host_prompt": leaked,
        "unresolved": unresolved,
        "supports_a_deletion_decision": not unresolved,
    }


def render(result: dict) -> str:
    head = (f"codex host-prompt census — discovered {result['discovered']}, "
            f"parsed {result['parsed']}, "
            f"skipped {result['discovered'] - result['parsed']}")
    lines = [head, f"  usable {result['usable']}"
             + (f" (cli >= {result['min_cli']})" if result["min_cli"] else "")
             + f", {result['distinct_prompts']} distinct prompts"]
    if result["stores"]:
        lines.append("  stores: " + ", ".join(
            f"{store}={n}" for store, n in sorted(result["stores"].items())))
    lines.append("")
    if result["coverage"]:
        width = max(len(label) for label, _, _ in CONTRACT_CLAUSES) + 4
        lines.append(f"{'session kind':14}{'n':>5}  " + "".join(
            f"{label:>{width}}" for label, _, _ in CONTRACT_CLAUSES))
        for kind, counts in sorted(result["coverage"].items()):
            n = counts["n"]
            lines.append(f"{kind:14}{n:>5}  " + "".join(
                f"{f'{counts[label]}/{n}':>{width}}"
                for label, _, _ in CONTRACT_CLAUSES))
        lines += ["", "Each column is the vendor text that would make one "
                      "contract clause a restatement:"]
        for label, clause, needle in CONTRACT_CLAUSES:
            lines.append(f"  {label:<16}{clause!r} <- {needle!r}")
        lines += [
            "",
            "A clause the thinnest consumer's prompt does not carry must stay",
            "in the contract, whatever a richer variant says. Both session",
            "kinds are handed AGENTS.contract.md as instructions, so subagent",
            "is the floor.",
        ]
    if result["unresolved"]:
        lines += ["", "UNRESOLVED — this sample cannot justify deleting a "
                      "contract clause:"]
        lines += [f"  - {reason}" for reason in result["unresolved"]]
        lines.append("  A smaller sample makes vendor coverage look more "
                     "complete than it is.")
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
    return 0 if result["supports_a_deletion_decision"] else 1


if __name__ == "__main__":
    sys.exit(main())
