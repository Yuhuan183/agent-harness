#!/usr/bin/env python3
"""Swap the deployed contract for one arm, and put it back. Nothing else.

`evals/traps/s11-pointer-redundancy` asked whether a contract clause naming a
skill does anything its own `description` does not, and answered it for two of
three clauses. The third, `baton-dispatch`, could not be answered there: its
trigger is an **action** — "once a dispatch is going ahead" — and that trap runs
headless under `--permission-mode manual`, where no action is ever approved. All
three fixtures were refused on correct grounds and the positive cell could only
ever return zero.

The replay harness does approve actions, so the question is askable there. What
it needs from s11 is the arm text, which `arms.py` already builds as pure
functions, and the safety around swapping a live `~/.claude/CLAUDE.md`, which is
what this module is.

Four guards, in order of how much they matter — the same four s11 uses, and
deliberately not shared with it. Refactoring a closed trap's restore path to
import this would put an untested indirection between a live user contract and
the code that puts it back, in exchange for nothing measurable.

1. **Refuse to start on pre-existing drift.** Restoring to a snapshot of an
   unexpected state would make that drift permanent and blame the experiment.
2. **Snapshot, then restore in `finally`.** Interrupts and crashes included.
3. **Verify the restore by hash**, not by having written it.
4. **Leave a sentinel while swapped**, so an interrupted run cannot be papered
   over by the next one.

    with contract_arm("baton-dispatch", "b") as state:
        ...                       # the contract is swapped for this block only
"""
from __future__ import annotations

import hashlib
import importlib.util
import shutil
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEPLOYED = Path.home() / ".claude" / "CLAUDE.md"
SOURCE = ROOT / "main" / "claude" / "CLAUDE.contract.md"
SENTINEL = Path.home() / ".claude" / ".replay-arm-in-progress"
ARMS = ROOT / "evals" / "traps" / "s11-pointer-redundancy" / "arms.py"


def _arms():
    """s11's arm builder, imported for its pure text functions only."""
    spec = importlib.util.spec_from_file_location("s11_arms", ARMS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def probe(clause: str) -> str:
    """The manipulation check for this clause, from the module that removed it."""
    return _arms().probe(clause)


def probes(clause: str, arm: str) -> list[tuple[str, str]]:
    """Every question this arm has to answer before the run is paid for.

    One question is enough while an arm removes one thing: it either left or it
    did not. The slim arm removes eleven bullets and keeps two, so it needs a
    question that fails in the other direction as well — proof that the rule
    under test survived the surgery. Without it, a drop in compliance cannot be
    told apart from having deleted the rule by accident, which is the one
    failure that would look exactly like the hypothesis being true.
    """
    if arm == "s":
        return list(_arms().SLIM_PROBES)
    return [(probe(clause), "YES" if arm == "a" else "NO")]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_no_drift(paths: "Paths | None" = None) -> None:
    paths = paths or Paths()
    DEPLOYED, SOURCE, SENTINEL = paths.deployed, paths.source, paths.sentinel
    if not DEPLOYED.exists():
        raise SystemExit(f"{DEPLOYED} does not exist; deploy before running")
    if SENTINEL.exists():
        raise SystemExit(
            f"{SENTINEL} exists: a previous arm did not restore. Run "
            "`scripts/sync.sh --apply`, confirm the contract matches source, "
            "then delete the sentinel. Refusing to stack a second swap.")
    if DEPLOYED.read_text(encoding="utf-8") != SOURCE.read_text(encoding="utf-8"):
        raise SystemExit(
            "deployed contract differs from repo source. Reconcile first "
            "(`scripts/sync.sh` to see the diff): restoring to a snapshot of "
            "an unexpected state would make that drift permanent.")


@dataclass(frozen=True)
class Paths:
    """Where the three files live. Injectable so the restore path can be tested.

    The live defaults are the point of the module, and they are also the reason
    the logic must be exercised somewhere else: a test that proves the restore
    works by swapping the operator's real contract is a test that can leave the
    machine broken when it fails, which is the opposite of what it is for.
    """

    deployed: Path = DEPLOYED
    source: Path = SOURCE
    sentinel: Path = SENTINEL


@contextmanager
def contract_arm(clause: str, arm: str, paths: "Paths | None" = None):
    """Deploy `arm` of `clause` for the duration of the block, then restore.

    Yields what the run actually had — the contract hash in effect and how many
    times the clause's name survives in it — because a run that records the arm
    it asked for rather than the bytes it got is the failure this whole line of
    work keeps rediscovering.
    """
    arms = _arms()
    paths = paths or Paths()
    DEPLOYED, SENTINEL = paths.deployed, paths.sentinel
    check_no_drift(paths)
    before = sha(DEPLOYED)
    snapshot = None
    try:
        if arm != "a":
            snapshot = Path(tempfile.mkdtemp(prefix="replay-arm-")) / "CLAUDE.md"
            shutil.copy2(DEPLOYED, snapshot)
            SENTINEL.write_text(f"{clause}\n{arm}\n{snapshot}\n", encoding="utf-8")
            DEPLOYED.write_text(
                arms.variant(DEPLOYED.read_text(encoding="utf-8"), clause, arm),
                encoding="utf-8")
            print(f"arm {arm.upper()}: {clause} "
                  f"({before[:12]} -> {sha(DEPLOYED)[:12]})", file=sys.stderr)
        text = DEPLOYED.read_text(encoding="utf-8")
        yield {"arm": arm, "clause": clause,
               "contract_sha256_in_effect": sha(DEPLOYED),
               "clause_name_mentions_in_effect": arms.names_remaining(text, clause)}
    finally:
        if snapshot is not None:
            shutil.copy2(snapshot, DEPLOYED)
            after = sha(DEPLOYED)
            if after == before:
                SENTINEL.unlink(missing_ok=True)
                shutil.rmtree(snapshot.parent, ignore_errors=True)
                print("contract restored and verified", file=sys.stderr)
            else:
                print(f"RESTORE FAILED: {DEPLOYED} is {after[:12]}, expected "
                      f"{before[:12]}. Snapshot kept at {snapshot}. "
                      "Recover with `scripts/sync.sh --apply`.", file=sys.stderr)
