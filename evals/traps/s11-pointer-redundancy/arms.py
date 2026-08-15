#!/usr/bin/env python3
"""Build an arm's contract text. Pure text in, pure text out.

This module never writes to `~/.claude`, never deploys, and never runs an agent
- `run.py` owns those - so the part of the experiment that can be reviewed by
reading stays separate from the part that touches a live configuration.

Three arms, because arm B answered a narrower question than it looked like:

    A  the contract as shipped
    B  the explicit "load <skill>" instruction removed, name may remain
    C  every mention of the skill removed

B tells you whether the *instruction* carries the loading. C tells you whether
the *name* does. Running only B and reading a null as "the contract contributes
nothing" would have skipped the alternative that the name alone is enough - and
on 2026-08-08 arm B came back 5/5 loaded on p1, which is exactly the result that
makes C worth paying for.

Refusing to guess is the design. Each removal is an exact literal; if the
contract has been reworded since these were recorded, the removal raises instead
of falling back to a fuzzy match. A near-miss would produce an arm that differs
from A in some way nobody wrote down, and the run would still look valid.

    arms.py --list
    arms.py --clause provider-routing --arm c
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

POINTER = {
    "headroom-protocol": (
        "- Load `headroom-protocol` only when Headroom MCP tools exist and "
        "an unusually large read-only blob repays manual compression.\n"
    ),
    "provider-routing": (
        "- Cross-provider dispatch, H/X profiles, GPT↔Claude fallback, "
        "security routing, and verifier triggers: load `provider-routing`.\n"
    ),
    "baton-dispatch": (
        " Once a dispatch is going ahead, load `baton-dispatch` — it owns "
        "the dispatch shape, batching rules, Plan convergence, fixed record "
        "formats, and the QC fraud checklist."
    ),
    # Not a pointer, and not here to be studied. This is the reverse control:
    # every arm run against this contract so far has come back null, and a null
    # is only readable if the apparatus can be shown to detect *something*. This
    # clause is the something — a rule with an effect nobody doubts, removed the
    # same way through the same code, so that "we saw no difference" can be
    # separated from "we would not have seen one".
    "language": (
        "- Respond in Traditional Chinese (Taiwan usage), in plain human "
        "language. Keep code, identifiers, commands, comments, and commit "
        "messages in English. Thinking and agent-to-agent briefs stay in "
        "precise, concise English — only user-facing replies switch to "
        "Traditional Chinese.\n"
    ),
}

# What arm C removes on top of the pointer, to erase the name entirely. Each
# entry also records the cost of doing so: removing a name can only be done by
# removing the clause that carries it, and for two of the three that clause says
# something else as well. A result from arm C is therefore never "the same
# contract minus a name" - it is that minus one weakened rule, stated here so a
# reader does not have to reconstruct it.
RESIDUAL = {
    "headroom-protocol": {
        "removals": (),
        "side_effect": None,
    },
    "provider-routing": {
        "removals": (", and only on a `provider-routing` trigger",),
        "side_effect": "the verifier clause loses its trigger condition, so arm "
                       "C also relaxes when an outcome verifier is allowed",
    },
    "baton-dispatch": {
        "removals": (" (formats and request sources in `baton-dispatch`)",),
        "side_effect": "the reporting clause loses its pointer to where the "
                       "record formats are defined",
    },
    "language": {
        "removals": (),
        "side_effect": "the clause names no skill, so B and C are the same "
                       "text and only B is worth running. Removing it also "
                       "removes the rules keeping code and agent-to-agent "
                       "briefs in English, because they share the bullet",
    },
}

# The manipulation check, per clause. Asking whether a skill is named is the
# right question for a pointer and the wrong one for a rule that names no skill:
# `language` would answer NO in both arms, and a check that cannot fail is not a
# check. Kept beside the removals, since the thing that knows what was taken out
# is the thing that should say how to ask whether it is gone.
PROBE = {
    None: ("Answer with exactly one word, YES or NO, and nothing else. Does "
           "your global working contract contain an explicit instruction to "
           "load a skill named `{clause}`?"),
    "language": ("Answer with exactly one word, YES or NO, and nothing else. "
                 "Does your global working contract tell you which language to "
                 "write your replies to the user in?"),
}


def probe(clause: str) -> str:
    return PROBE.get(clause, PROBE[None]).format(clause=clause)


def variant(contract: str, clause: str, arm: str) -> str:
    """The contract for one arm, or a hard failure naming what did not match."""
    if clause not in POINTER:
        raise SystemExit(f"unknown clause {clause!r}; try --list")
    if arm == "a":
        return contract
    if arm not in ("b", "c"):
        raise SystemExit(f"unknown arm {arm!r}")

    literals = [POINTER[clause]]
    if arm == "c":
        literals += list(RESIDUAL[clause]["removals"])

    result = contract
    for literal in literals:
        count = result.count(literal)
        if count != 1:
            raise SystemExit(
                f"{clause} arm {arm}: expected this text exactly once, found "
                f"{count}:\n  {literal!r}\nThe contract was reworded after this "
                "removal was recorded. Re-record the literal rather than "
                "loosening the match, or the arm will differ from A in a way "
                "nobody wrote down.")
        result = result.replace(literal, "", 1)
    return result


def names_remaining(contract: str, clause: str) -> int:
    return contract.count(f"`{clause}`")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--clause")
    parser.add_argument("--arm", default="b", choices=("a", "b", "c"))
    parser.add_argument("--contract", type=Path,
                        default=ROOT / "main" / "claude" / "CLAUDE.contract.md")
    args = parser.parse_args()

    contract = args.contract.read_text(encoding="utf-8")

    if args.list:
        for name in POINTER:
            b = variant(contract, name, "b")
            c = variant(contract, name, "c")
            print(f"{name}")
            print(f"   A: {names_remaining(contract, name)} mention(s)")
            print(f"   B: {names_remaining(b, name)} mention(s) remain")
            print(f"   C: {names_remaining(c, name)} mention(s) remain"
                  + (f"  [side effect: {RESIDUAL[name]['side_effect']}]"
                     if RESIDUAL[name]["side_effect"] else ""))
        return 0
    if not args.clause:
        parser.error("--clause or --list")

    text = variant(contract, args.clause, args.arm)
    print(text, end="")
    print(f"\n<!-- arm {args.arm}: {len(contract) - len(text)} bytes removed, "
          f"{names_remaining(text, args.clause)} mention(s) of the name remain -->",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
