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
    # Here as the reverse control, not as a pointer to study: every arm run
    # against this contract so far has come back null, and a null is only
    # readable if the apparatus can be shown to detect *something*. This clause
    # is the something — a rule with an effect nobody doubts, removed the same
    # way through the same code, so that "we saw no difference" can be separated
    # from "we would not have seen one".
    #
    # Re-recorded 2026-08-19, when the clause gained a register split: the
    # language rule now sends user-facing prose to `speak-human-tw`'s standard.
    # That makes it a pointer as well as the control, which is a change to what
    # arm C means here rather than to what the control does — the language switch
    # is still what arm B removes and still what nobody doubts.
    "language": (
        "- Respond in Traditional Chinese (Taiwan usage). Keep code, "
        "identifiers, commands, comments, and commit messages in English. "
        "Thinking and agent-to-agent briefs stay in precise, concise English; "
        "only user-facing replies switch to Traditional Chinese, and those "
        "answer to `speak-human-tw`'s standard for prose a person reads.\n"
    ),
    # Also not a pointer. This one is here because it is the only resident
    # clause found so far whose value can be priced on the quality of what gets
    # delivered rather than on whether a marker appeared. The dispatch line
    # closed on a structural argument — isolation subtracts information, so an
    # answer-checkable task cannot reward it — and that argument does not reach
    # this clause: running the code *adds* an observation no amount of reading
    # produces, so an answer-checkable task is exactly where it can be measured.
    "verification": (
        "- Run the narrowest verification that could actually refute the claim "
        "you are about to make.\n"
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
        "side_effect": "B and C are still the same text, and from 2026-08-19 for "
                       "a different reason: the clause does name a skill now, but "
                       "the name sits inside the bullet B already removes whole, "
                       "and arm C is B's removal plus extras rather than a "
                       "narrower cut. Studying this pointer would need an arm "
                       "that keeps the bullet and drops only the sentence naming "
                       "`speak-human-tw`, which is not what C is. Removing the "
                       "bullet also removes the rules keeping code and "
                       "agent-to-agent briefs in English, because they share it",
    },
    "verification": {
        "removals": (),
        "side_effect": "the clause names no skill, so B and C are the same "
                       "text and only B is worth running. It is one sentence "
                       "carrying one rule, so removing it removes nothing "
                       "else — the cleanest removal in this table",
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
    "verification": ("Answer with exactly one word, YES or NO, and nothing "
                     "else. Does your global working contract tell you to run "
                     "a check that could refute a claim before you make it?"),
}


def probe(clause: str) -> str:
    return PROBE.get(clause, PROBE[None]).format(clause=clause)


# The bullet whose compliance a dilution test measures, kept verbatim.
DECISION_MATERIAL = (
    "- Mark a material choice made without user input as "
    "`DECISION: <what and why>`; mark uncertainty only when it could change "
    "the conclusion.\n"
)

DECISION_OPERATIONAL = (
    "- Mark any choice the request did not specify as "
    "`DECISION: <what and why>`; mark uncertainty only when it could change "
    "the conclusion.\n"
)


def decision_bullet(contract: str) -> str:
    """Whichever of the two wordings this contract actually carries.

    Both are here because the operational one shipped on 2026-08-16, on the
    strength of `m1` (14/92 against 44/91). Before that the module named the
    material wording as *the* bullet and every arm hard-coded it, which was
    fine right up until the thing it hard-coded stopped being deployed.

    Resolving it from the contract instead means an arm is defined by the
    contrast it creates rather than by which side of that contrast happens to
    be shipped this month — so these arms survive the contract flipping back,
    and a run's `meta.json` still records which bytes it actually had.
    """
    present = [text for text in (DECISION_MATERIAL, DECISION_OPERATIONAL)
               if contract.count(text) == 1]
    if len(present) != 1 or sum(contract.count(text) for text in
                                (DECISION_MATERIAL, DECISION_OPERATIONAL)) != 1:
        raise SystemExit(
            "the DECISION bullet is missing, duplicated, or carries a wording "
            "this module does not know. The contract changed under the arms: "
            "update DECISION_MATERIAL/DECISION_OPERATIONAL before running, "
            "because an arm that silently swaps in a retired wording measures "
            "the retirement rather than the manipulation.")
    return present[0]


def slim(contract: str) -> str:
    """The contract reduced to the two bullets a dilution test needs.

    Every clause-removal arm so far asks whether *that* clause did anything.
    None of them asks the question underneath: whether a contract carrying
    clauses that do nothing makes the ones that do work worse. That is the only
    cost that could justify deleting a clause at all — 35 tokens out of a
    million-token context is not a reason, and this repo has never measured
    whether attention is the real currency.

    So: keep the rule under test and the rule that holds the reply surface
    fixed, drop the other eleven bullets and both other sections. The two arms
    then differ only in clauses that are candidates for deletion, and any
    difference in compliance with a *kept* rule is dilution.

    Kept verbatim rather than paraphrased, and checked: a slim contract that
    reworded the rule under test would measure the rewording.
    """
    keep = (POINTER["language"], decision_bullet(contract))
    lines = contract.splitlines(keepends=True)
    out = [line for line in lines
           if line.startswith("# ") or line.startswith("## Working agreement")]
    out.append("\n")
    out.extend(keep)
    slimmed = "".join(out)

    for literal in keep:
        if slimmed.count(literal) != 1:
            raise SystemExit("slim: a kept bullet is missing or duplicated; "
                             "the contract was reworded under this function")
    if len(slimmed) >= len(contract):
        raise SystemExit("slim: nothing was removed")
    return slimmed


# The same rule with the judgement call taken out of it.
#
# 2026-08-16: all thirty `m1` runs introduced a module-level constant the
# request never asked for, and eight said so. Same model, same prompt, same
# choice, marked a quarter of the time — which is not a coherent threshold for
# the word "material", it is variance in whether the rule fires at all. The
# eight that did mark it described a structural choice; not one of them marked
# the constant's *name*, which split three ways across the thirty.
#
# So this arm changes exactly one thing: the qualifier the model has to judge
# becomes a test it can apply. Everything else in the bullet is byte-identical,
# because an arm that reworded two things would not say which one moved.
# For the slim arm the manipulation check has to fail in both directions. One
# question proves the removal landed; the other proves the rule under test
# survived it, and without the second a drop in compliance is indistinguishable
# from having deleted the rule by accident.
def reworded(contract: str) -> str:
    """The `DECISION:` rule swapped for the wording the contract does not use.

    Named for what it did when it was written — take the judgement call out of
    the rule — and now defined by contrast, because the wording it used to
    install is the one that ships. Run against today's contract it puts the
    judgement call *back*, which is the only version of this arm that still has
    a control to be compared against.
    """
    present = decision_bullet(contract)
    other = (DECISION_OPERATIONAL if present == DECISION_MATERIAL
             else DECISION_MATERIAL)
    return contract.replace(present, other)


# A rewording arm cannot be checked by asking whether the rule is present — it
# is present in both arms, which is the point. The question has to name the part
# that changed.
# Each side of the contrast gets one question, and an arm's expectations are
# the mirror of what it installed. Written as functions of the contract rather
# than as constants because the arm itself is now a contrast: fixed answers
# would have quietly inverted on 2026-08-16, when the wording this arm used to
# install became the wording it is run against.
MATERIAL_QUESTION = (
    "Answer with exactly one word, YES or NO, and nothing else. Does your "
    "global working contract use the word \"material\" when it tells you which "
    "choices to mark?"
)
UNSPECIFIED_QUESTION = (
    "Answer with exactly one word, YES or NO, and nothing else. Does your "
    "global working contract tell you to mark a choice the request did not "
    "specify regardless of whether you judge that choice to be material?"
)
# The qualifier is in the question because the first draft was not, and it only
# worked in one direction. It asked whether the contract says to mark a choice
# the request did not specify — true under *both* wordings, since marking a
# material unspecified choice is also marking an unspecified choice. Measured
# 2026-08-17 when the arm first ran inverted: the model answered YES where NO
# was expected, `run.py` refused the run, and the contract was restored.
#
# That is the manipulation check doing exactly its job, on itself. No published
# result used this pair in the inverted direction — `r2`'s arm W ran it the
# original way and both probes landed 10 times out of 10 — so nothing needs
# recomputing, only the question needed to become one that can answer NO.
KEPT_MATERIAL_QUESTION = (
    "Answer with exactly one word, YES or NO, and nothing else. Does your "
    "global working contract tell you to mark a material choice you made "
    "without user input?"
)
DELEGATE_QUESTION = (
    "Answer with exactly one word, YES or NO, and nothing else. Does your "
    "global working contract give you any rule about when to delegate work to "
    "a subagent?"
)


def reword_probes(contract: str) -> tuple[tuple[str, str], ...]:
    """The two-sided check for the reword arm, against what the arm installs.

    The rewording arm cannot be checked by asking whether the rule is present:
    it is present in both arms, which is the point. So one question names the
    part that changed and the other names the part that replaced it, and the
    pair has to answer in opposite directions or the swap did not land.
    """
    # `contract` is what the session will actually read, which means `run.py`
    # has *already* swapped it before asking. The first draft computed the
    # expectations as though it were reading the pre-swap contract, so both
    # answers came back exactly inverted — measured 2026-08-17, on the first
    # run that ever exercised this arm in the inverted direction.
    #
    # `r2`'s arm W batch is unaffected: it ran before these probes became
    # functions, against the fixed pair, and both landed 10 times out of 10.
    # Nothing published needs recomputing; the guard refused every run that
    # would have needed it.
    in_effect_is_material = decision_bullet(contract) == DECISION_MATERIAL
    return ((MATERIAL_QUESTION, "YES" if in_effect_is_material else "NO"),
            (UNSPECIFIED_QUESTION, "NO" if in_effect_is_material else "YES"))


def slim_probes(contract: str) -> tuple[tuple[str, str], ...]:
    """The two-sided check for the slim arm, against the bullet it keeps.

    One question proves the removal landed; the other proves the rule under
    test survived it, without which a drop in compliance is indistinguishable
    from having deleted the rule by accident. The second question follows the
    deployed wording, because `slim` keeps the bullet verbatim and asking about
    a retired wording would fail for the one reason that is not a finding.
    """
    kept = decision_bullet(contract)
    return ((DELEGATE_QUESTION, "NO"),
            (KEPT_MATERIAL_QUESTION if kept == DECISION_MATERIAL
             else UNSPECIFIED_QUESTION, "YES"))


def variant(contract: str, clause: str, arm: str) -> str:
    """The contract for one arm, or a hard failure naming what did not match."""
    if clause not in POINTER:
        raise SystemExit(f"unknown clause {clause!r}; try --list")
    if arm == "a":
        return contract
    if arm == "s":
        return slim(contract)
    if arm == "w":
        return reworded(contract)
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
