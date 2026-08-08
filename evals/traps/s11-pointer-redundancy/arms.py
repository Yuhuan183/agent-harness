#!/usr/bin/env python3
"""Build the arm-B contract text: the same contract with one pointer removed.

Pure text in, pure text out. This module never writes to `~/.claude`, never
deploys, and never runs an agent - `run.py` owns those, so that the part of the
experiment that can be reviewed by reading is separate from the part that
touches a live configuration.

Refusing to guess is the whole design here. Each removal is an exact literal:
if the contract has been reworded since these were recorded, the removal raises
instead of falling back to a fuzzy match. A near-miss edit would produce an
arm B that differs from arm A in some way nobody wrote down, and the run would
still look valid.

    arms.py --list
    arms.py --clause headroom-protocol --contract main/claude/CLAUDE.contract.md
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

# The exact text arm B removes, and what stays behind. `clean` records whether
# the skill's name survives elsewhere in the contract, because that decides
# which question a result actually answers - see GROUND-TRUTH.md.
REMOVALS = {
    "headroom-protocol": {
        "clean": True,
        "remaining": None,
        "text": (
            "- Load `headroom-protocol` only when Headroom MCP tools exist and "
            "an unusually large read-only blob repays manual compression.\n"
        ),
    },
    "provider-routing": {
        "clean": False,
        "remaining": "the verifier-trigger clause still names the skill",
        "text": (
            "- Cross-provider dispatch, H/X profiles, GPT↔Claude fallback, "
            "security routing, and verifier triggers: load `provider-routing`.\n"
        ),
    },
    "baton-dispatch": {
        "clean": False,
        "remaining": "the reporting clause still names the skill",
        "text": (
            " Once a dispatch is going ahead, load `baton-dispatch` — it owns "
            "the dispatch shape, batching rules, Plan convergence, fixed record "
            "formats, and the QC fraud checklist."
        ),
    },
}


def arm_b(contract: str, clause: str) -> str:
    """The contract with exactly one pointer removed, or a hard failure."""
    if clause not in REMOVALS:
        raise SystemExit(f"unknown clause {clause!r}; try --list")
    literal = REMOVALS[clause]["text"]
    count = contract.count(literal)
    if count != 1:
        raise SystemExit(
            f"{clause}: expected the recorded clause exactly once, found "
            f"{count}. The contract was reworded after this removal was "
            "written; re-record the literal rather than loosening the match, "
            "or arm B will differ from arm A in an unrecorded way.")
    return contract.replace(literal, "", 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--clause")
    parser.add_argument("--contract", type=Path,
                        default=ROOT / "main" / "claude" / "CLAUDE.contract.md")
    args = parser.parse_args()

    if args.list:
        for name, spec in REMOVALS.items():
            kind = "clean" if spec["clean"] else f"confounded: {spec['remaining']}"
            print(f"{name:<20} {kind}")
        return 0
    if not args.clause:
        parser.error("--clause or --list")

    contract = args.contract.read_text(encoding="utf-8")
    variant = arm_b(contract, args.clause)
    removed = len(contract) - len(variant)
    print(variant, end="")
    print(f"\n<!-- arm B: removed {removed} bytes for {args.clause} -->",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
