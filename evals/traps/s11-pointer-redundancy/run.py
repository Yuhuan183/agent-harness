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
import importlib.util
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
from arms import POINTER, variant  # noqa: E402


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


def claude(prompt: str, workdir: Path, mcp: str | None = None) -> tuple[int, str]:
    """One headless turn, outside any project so no project CLAUDE.md leaks in."""
    argv = [
        "claude", "--print", prompt,
        "--output-format", "stream-json", "--verbose",
        # The machine's own hooks are not part of this construct.
        "--settings", json.dumps({"hooks": {}}),
        "--permission-mode", "manual",
        # Always strict: this flag is what makes `--mcp-config` a replacement
        # rather than an addition. Passing them as alternatives - strict when no
        # server was wanted, `--mcp-config` alone when one was - meant the
        # headroom cells loaded the operator's entire MCP surface on top of the
        # one server they asked for. Caught 2026-08-10 four runs in: the session
        # listed pencil, serena, Figma and four Google servers alongside
        # headroom, and 63 tools where the other cells see a minimal set.
        "--strict-mcp-config",
    ]
    if mcp:
        # Option A, chosen 2026-08-08. The `headroom-protocol` clause is
        # conditional on Headroom MCP tools existing, so under an empty MCP
        # config the correct behaviour in *both* arms is to not load, and the
        # cell measures nothing. Attaching the real server is the only way to
        # reproduce the trigger, and it costs some isolation - the server
        # definition comes from this machine - but with strict set, that is the
        # only thing it costs.
        argv += ["--mcp-config", mcp]
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


def session_environment(stdout: str) -> dict[str, object]:
    """What the run actually had, read back out of its own event stream.

    Asking for a condition and getting it are different things, and this fixture
    has now confused them four times - a marker a file read could satisfy, a
    driver that discarded the swap confirmation, an `--mcp-config` that added
    servers instead of replacing them, and a planted token that was not unique.
    Three were caught by hand afterwards. Recording the condition rather than
    the intent is what makes the fourth kind visible without anyone remembering
    to look.
    """
    servers, tools = None, None
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event.get("mcp_servers"), list):
            servers = [{"name": s.get("name"), "status": s.get("status")}
                       for s in event["mcp_servers"]]
        if event.get("type") == "system" and isinstance(event.get("tools"), list):
            tools = event["tools"]
    return {
        "mcp_servers_in_session": servers,
        "tool_count_in_session": len(tools) if tools is not None else None,
    }


def build_fixture(scenario_stem: str, workdir: Path) -> list[str]:
    spec = importlib.util.spec_from_file_location(
        "s11_fixtures", HERE / "fixtures" / "build.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build(scenario_stem, workdir)


def mcp_config_for(scenario_text: str, workdir: Path) -> str | None:
    """The path to an MCP config when a scenario declares it needs one.

    Written fresh from the machine's own `~/.claude.json` entry rather than kept
    in the repo: an MCP server definition can carry a local path or a token, and
    neither belongs in a fixture. Written *into the run's own directory* for the
    same reason - that directory is deleted when the run ends, whereas the first
    version used `delete=False` in the system temp dir and would have left one
    copy of the server definition behind per run (caught by audit before any
    headroom cell ran, so nothing leaked).
    """
    match = re.search(r"^needs_mcp:\s*(\S+)", scenario_text, re.M)
    if not match:
        return None
    server = match.group(1)
    source = json.loads((Path.home() / ".claude.json").read_text(encoding="utf-8"))
    entry = (source.get("mcpServers") or {}).get(server)
    if entry is None:
        raise SystemExit(
            f"scenario needs the {server!r} MCP server and this machine has no "
            "such entry; the cell cannot reproduce its own trigger condition")
    target = workdir / ".s11-mcp.json"
    target.write_text(json.dumps({"mcpServers": {server: entry}}),
                      encoding="utf-8")
    return str(target)


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
        if arm in ("b", "c"):
            snapshot = Path(tempfile.mkdtemp(prefix="s11-snapshot-")) / "CLAUDE.md"
            shutil.copy2(DEPLOYED, snapshot)
            SENTINEL.write_text(f"{clause}\n{snapshot}\n", encoding="utf-8")
            DEPLOYED.write_text(
                variant(DEPLOYED.read_text(encoding="utf-8"), clause, arm),
                encoding="utf-8")
            print(f"arm {arm.upper()}: {clause} "
                  f"({before[:12]} -> {sha(DEPLOYED)[:12]})", file=sys.stderr)

        with tempfile.TemporaryDirectory(prefix="s11-work-") as work:
            workdir = Path(work)
            if do_preflight and not preflight(clause, arm, workdir):
                print("manipulation check failed; not running the scenario",
                      file=sys.stderr)
                return 2
            if scenario is None:
                return 0
            text = scenario.read_text(encoding="utf-8")
            body = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)
            # The files the scenario talks about have to be there. Without them
            # the agent spends its one turn discovering they are missing, which
            # is not the branch under test (dry run, 2026-08-08).
            built = build_fixture(scenario.stem, workdir)
            if built:
                print(f"fixture: {', '.join(built)}", file=sys.stderr)
            mcp = mcp_config_for(text, workdir)
            # Provenance, written from the live file at the moment of the call.
            # The 2026-08-08 pilot recorded none, so every arm-B row was a claim
            # about a condition nothing in the artifacts could confirm - the
            # exact failure the surface fingerprints exist to prevent, repeated
            # one level down. The post-run diff proves the contract was restored;
            # only this proves what it was during the call.
            in_effect = sha(DEPLOYED)
            names_left = DEPLOYED.read_text(encoding="utf-8").count(f"`{clause}`")
            code, stdout = claude(body.strip(), workdir, mcp)
            if out:
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(stdout, encoding="utf-8")
                out.with_suffix(".meta.json").write_text(json.dumps({
                    "clause": clause, "arm": arm,
                    "scenario": scenario.name,
                    "contract_sha256_in_effect": in_effect,
                    "clause_name_mentions_in_effect": names_left,
                    "mcp_requested": bool(mcp),
                    **session_environment(stdout),
                    "exit": code,
                }, indent=2), encoding="utf-8")
                print(f"events -> {out} (contract {in_effect[:12]}, "
                      f"{names_left} mention(s))", file=sys.stderr)
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
    parser.add_argument("--clause", required=True, choices=sorted(POINTER))
    parser.add_argument("--arm", required=True, choices=("a", "b", "c"))
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
        text = variant(current, args.clause, args.arm)
        print(f"deployed  {sha(DEPLOYED)[:12]}  {len(current)} bytes")
        print(f"arm {args.arm}      "
              f"{hashlib.sha256(text.encode()).hexdigest()[:12]}  "
              f"{len(text)} bytes")
        print("nothing was written")
        return 0

    return run_arm(args.clause, args.arm, args.scenario, args.out,
                   args.preflight)


if __name__ == "__main__":
    sys.exit(main())
