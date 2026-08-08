#!/usr/bin/env python3
"""Run one s11 arm. Arm B swaps the deployed contract, and puts it back.

Arm A needs no configuration change: it is the machine as it already is. Arm B
has to remove a clause from `~/.claude/CLAUDE.md`, because that file is the
surface under test and there is no way to vary it from the command line - an
isolated `HOME` loses the credentials (probed 2026-08-08: "Not logged in").
`evals/scripts/rung-run.py` deliberately avoids touching `~/.claude` for exactly
the reason this script cannot: it "leaves a restore step nobody can be trusted
to remember". So the restore is not left to anybody.

Four things guard it, in order of how much they matter:

1. **Refuse to start on pre-existing drift.** If the deployed file already
   differs from the repo source, this script stops. Restoring to a snapshot of
   an unexpected state would quietly make the drift permanent and blame it on
   the experiment.
2. **Snapshot, then restore in `finally`.** Interrupts and crashes included.
3. **Verify the restore by hash**, not by having written it. If it does not
   match, say so loudly and name the recovery command rather than exiting 0.
4. **Leave a breadcrumb while swapped.** A sentinel file exists only between the
   swap and the restore; a later run refuses to start while it is there, so an
   interrupted run cannot be papered over by the next one.

The manipulation check is not optional. Arm B is only meaningful if the clause
actually left the agent's context, so `--preflight` asks the model whether the
contract contains the instruction and compares the answer to the arm. A run
whose manipulation did not land is not a data point.

    run.py --clause headroom-protocol --arm a --scenario scenarios/h1-large-blob.md
    run.py --clause headroom-protocol --arm b --preflight
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DEPLOYED = Path.home() / ".claude" / "CLAUDE.md"
SOURCE = ROOT / "main" / "claude" / "CLAUDE.contract.md"
SENTINEL = Path.home() / ".claude" / ".s11-arm-b-in-progress"

sys.path.insert(0, str(HERE))
from arms import REMOVALS, arm_b  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_no_drift() -> None:
    if not DEPLOYED.exists():
        raise SystemExit(f"{DEPLOYED} does not exist; deploy before running")
    if SENTINEL.exists():
        raise SystemExit(
            f"{SENTINEL} exists: a previous arm B did not restore. Run "
            "`scripts/sync.sh --apply`, confirm the contract matches source, "
            "then delete the sentinel. Refusing to stack a second swap.")
    if DEPLOYED.read_text(encoding="utf-8") != SOURCE.read_text(encoding="utf-8"):
        raise SystemExit(
            "deployed contract differs from repo source. Reconcile first "
            "(`scripts/sync.sh` to see the diff): restoring to a snapshot of an "
            "unexpected state would make that drift permanent.")


def claude(prompt: str, workdir: Path) -> tuple[int, str]:
    """One headless turn, outside any project so no project CLAUDE.md leaks in."""
    argv = [
        "claude", "--print", prompt,
        "--output-format", "stream-json", "--verbose",
        # The machine's own hooks and MCP servers are not part of this construct.
        "--settings", json.dumps({"hooks": {}}),
        "--strict-mcp-config",
        "--permission-mode", "manual",
    ]
    env = {**os.environ}
    env.pop("ANTHROPIC_BASE_URL", None)
    done = subprocess.run(argv, cwd=workdir, capture_output=True, text=True,
                          env=env, timeout=900)
    return done.returncode, done.stdout


PROBE = (
    "Answer with exactly one word, YES or NO, and nothing else. Does your "
    "global working contract contain an explicit instruction to load a skill "
    "named `{clause}`?"
)


def preflight(clause: str, arm: str, workdir: Path) -> bool:
    code, out = claude(PROBE.format(clause=clause), workdir)
    answer = "YES" if re.search(r"\bYES\b", out, re.I) else (
        "NO" if re.search(r"\bNO\b", out, re.I) else "?")
    expected = "YES" if arm == "a" else "NO"
    ok = answer == expected
    print(json.dumps({"preflight": "manipulation-check", "clause": clause,
                      "arm": arm, "answer": answer, "expected": expected,
                      "landed": ok, "exit": code}, indent=2))
    return ok


def run_arm(clause: str, arm: str, scenario: Path | None, out: Path | None,
            do_preflight: bool) -> int:
    check_no_drift()
    snapshot = None
    before = sha(DEPLOYED)
    try:
        if arm == "b":
            snapshot = Path(tempfile.mkdtemp(prefix="s11-snapshot-")) / "CLAUDE.md"
            shutil.copy2(DEPLOYED, snapshot)
            SENTINEL.write_text(f"{clause}\n{snapshot}\n", encoding="utf-8")
            DEPLOYED.write_text(
                arm_b(DEPLOYED.read_text(encoding="utf-8"), clause),
                encoding="utf-8")
            print(f"arm B: removed {clause} clause "
                  f"({before[:12]} -> {sha(DEPLOYED)[:12]})", file=sys.stderr)

        with tempfile.TemporaryDirectory(prefix="s11-work-") as work:
            workdir = Path(work)
            if do_preflight and not preflight(clause, arm, workdir):
                print("manipulation check failed; not running the scenario",
                      file=sys.stderr)
                return 2
            if scenario is None:
                return 0
            body = re.sub(r"\A---\n.*?\n---\n", "",
                          scenario.read_text(encoding="utf-8"), flags=re.S)
            code, stdout = claude(body.strip(), workdir)
            if out:
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(stdout, encoding="utf-8")
                print(f"events -> {out}", file=sys.stderr)
            return code
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clause", required=True, choices=sorted(REMOVALS))
    parser.add_argument("--arm", required=True, choices=("a", "b"))
    parser.add_argument("--scenario", type=Path)
    parser.add_argument("--out", type=Path, help="write the event stream here")
    parser.add_argument("--preflight", action="store_true",
                        help="run the manipulation check first (required for a "
                             "run that will be recorded)")
    parser.add_argument("--dry-run", action="store_true",
                        help="show the swap without touching anything")
    args = parser.parse_args()

    if args.dry_run:
        check_no_drift()
        current = DEPLOYED.read_text(encoding="utf-8")
        variant = arm_b(current, args.clause) if args.arm == "b" else current
        print(f"deployed  {sha(DEPLOYED)[:12]}  {len(current)} bytes")
        print(f"arm {args.arm}      "
              f"{hashlib.sha256(variant.encode()).hexdigest()[:12]}  "
              f"{len(variant)} bytes")
        print("nothing was written")
        return 0

    return run_arm(args.clause, args.arm, args.scenario, args.out,
                   args.preflight)


if __name__ == "__main__":
    sys.exit(main())
