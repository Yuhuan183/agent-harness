#!/usr/bin/env python3
"""Run one lifecycle-replay scenario as a real multi-turn session.

Why this is not a trap runner. The traps in `evals/traps/` ask a one-turn
question of a fresh session, which is why `s11/run.py` can pass
`--permission-mode manual`: nothing it measures needs the agent to write
anything. The three things replay exists to measure — recovery after an
interrupt, compliance across successive corrections, and what happens to
conflicting leaf results — are all properties of a session that runs, is
interrupted, is corrected, and dispatches. None of them survive being asked
once with nothing approved. s11's `b1` cell proved that from the other side on
2026-08-12: its positive cell could only ever return zero, because the clause
under test triggers on an *action* the harness forbade.

So this runner takes the opposite settings, each one measured rather than
assumed (2026-08-12, Claude Code 2.1.226):

    --session-id / --resume    turn 2 recalled turn 1 with no tool available,
                               including a turn that had been SIGINT'ed
    --permission-mode acceptEdits   writes land; under `manual` nothing does
    SIGINT at a wall clock     an interrupt lands mid-work and the session
                               still resumes afterwards
    cwd outside ~/.claude      a write under ~/.claude is refused outright

Two conditions this runner deliberately does *not* try to control, because a
probe showed the control does not exist:

1. **The machine's hooks are live.** `--settings '{"hooks":{}}'` does not
   suppress them — `--settings` loads *additional* settings, and a run launched
   with that flag still fired `SubagentStart`/`SubagentStop`. The only flag that
   silences user hooks, `--setting-sources project,local`, also drops the user
   contract (measured: the same probe answered `CONTRACT=NO`). Contract and
   hooks arrive together or not at all, so replay keeps both and says so.
2. **Therefore the run stages real dispatch stubs.** They are diverted, not
   suppressed: `AGENT_EXPERIENCE_PENDING` and `AGENT_EXPERIENCE_LEDGER` are
   pointed into the run's own directory, which keeps the machine's ledger clean
   *and* makes criterion 3 recomputable per run from that run's own artifacts —
   which is what criterion 4 asks for and what a global ledger cannot give.

Everything the grader needs is retained under `--out`: the event stream, a
snapshot of the workdir after every turn (an interrupted turn's snapshot is
taken before this runner touches anything), the diverted telemetry, and a
`meta.json` recording the conditions the run actually had.

    run.py --scenario scenarios/r1-interrupted-resume.md --out runs/r1-001
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from arm import contract_arm, probes as contract_probes  # noqa: E402
DEPLOYED = Path.home() / ".claude" / "CLAUDE.md"
SOURCE = ROOT / "main" / "claude" / "CLAUDE.contract.md"
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
TURN = re.compile(r"^##\s+turn\s+(\d+)\s*$", re.M)
# One turn's ceiling. 900 s was enough for every pilot and not enough on
# 2026-08-12, when five leaf dispatches came back `529 Overloaded` and the
# retries ate the budget: the turn was killed mid-sentence and graded as a
# failure until `grade.py` learned to gate on criterion 1. The ceiling exists
# so a wedged run cannot hang a batch, not to bound normal work, so it is set
# well above what a healthy turn needs.
TURN_TIMEOUT = 2400

# Asked of the model itself, not of the file, because the question is whether
# the manipulation reached the agent. The wording now comes from `arms.py`,
# which is where the removal is recorded: s11's question is still the default
# and still unchanged for every pointer clause, but it asks whether a *skill* is
# named, and a clause that names no skill would answer NO in both arms. A check
# that cannot fail is not a check.


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def surface_fingerprint() -> str | None:
    """This suite's measured-surface fingerprint, recorded by the run itself.

    Typed by hand three times on 2026-08-13 and wrong twice — once naming a
    value computed before a later edit to `grade.py`, once naming one computed
    before this scenario existed. Both were caught, which is luck rather than
    method. A fingerprint that a run writes into its own `meta.json` at the
    moment it runs cannot drift from what it describes, and `summarise.py`
    reads it back rather than trusting a README.
    """
    try:
        spec = importlib.util.spec_from_file_location(
            "trap_surface", ROOT / "evals" / "scripts" / "trap-surface.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.fingerprint("replay")[0][:module.SHORT]
    except Exception:            # never let bookkeeping fail a paid run
        return None


def drift_sources() -> dict[str, Path]:
    """Every deployed thing this suite fingerprints, mapped to where it deploys.

    The drift warning used to name one file. Skills joined the surface on
    2026-08-17, and a session reads them from `~/.claude/skills`, an rsync copy
    with its own inode - so a description edited in the repo moves the
    fingerprint while the session keeps reading the old body, silently. The
    surface decides what belongs here, so adding a deployed file to `surface.tsv`
    cannot leave its drift unchecked.
    """
    mapping: dict[str, Path] = {"main/claude/CLAUDE.contract.md": DEPLOYED}
    try:
        spec = importlib.util.spec_from_file_location(
            "trap_surface", ROOT / "evals" / "scripts" / "trap-surface.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        listed = module.surface_paths("replay")
    except Exception:                       # never let bookkeeping fail a run
        return mapping
    for path in listed:
        if path.startswith("main/claude/skills/"):
            name = Path(path).parent.name
            mapping[path] = Path.home() / ".claude" / "skills" / name / "SKILL.md"
    return mapping


def drifted() -> list[str]:
    """Sources whose deployed copy differs, or is missing."""
    out = []
    for source, deployed in drift_sources().items():
        origin = ROOT / source
        if not origin.exists():
            continue
        if not deployed.exists() or sha(deployed) != sha(origin):
            out.append(source)
    return out


def resident_skills() -> list[str]:
    """Every skill installed for the session, not only the ones this repo ships.

    Selection happens across the whole pool. On 2026-08-17 that was 49 skills of
    which this repo manages 8, and one of the other 41 - `debug-issue`,
    "systematically debug issues using graph-powered code navigation" - is a near
    duplicate of `evidence-debugging`. A batch that removes a competitor to test
    for crowding has to be distinguishable afterwards from one that did not, and
    `surface.tsv` cannot do it: the surface fingerprints repo files and the pool
    is machine state. So the run writes it down.
    """
    root = Path.home() / ".claude" / "skills"
    if not root.is_dir():
        return []
    return sorted(d.name for d in root.iterdir() if (d / "SKILL.md").is_file())


def parse_scenario(path: Path) -> tuple[dict, list[str]]:
    """Frontmatter plus the turns, in order.

    The frontmatter is the pre-registration: `marker`, `recovery_point` and
    `expect` are what the scenario committed to before any run, and the grader
    reads them from here rather than from anything written afterwards.
    """
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER.search(text)
    if not match:
        raise SystemExit(f"{path}: no frontmatter; a scenario without a "
                         "declared marker cannot be graded")
    spec: dict[str, str] = {}
    key = None
    for line in match.group(1).splitlines():
        if line.lstrip().startswith("#"):               # why a value is what it is
            continue
        if re.match(r"^\s+\S", line) and key:           # folded continuation
            spec[key] = f"{spec[key]} {line.strip()}"
        elif ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            spec[key] = value.strip()
    for required in ("id", "fixture", "marker", "recovery_point", "expect"):
        if required not in spec:
            raise SystemExit(f"{path}: frontmatter is missing {required}")

    body = text[match.end():]
    parts = TURN.split(body)
    if len(parts) < 3:
        raise SystemExit(f"{path}: no `## turn N` sections")
    turns = [chunk.strip() for chunk in parts[2::2]]
    if any(not turn for turn in turns):
        raise SystemExit(f"{path}: a turn is empty")
    return spec, turns


def build_fixture(name: str, workdir: Path) -> list[str]:
    spec = importlib.util.spec_from_file_location(
        "replay_fixtures", HERE / "fixtures" / "build.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build(name, workdir)


def child_env(run_dir: Path, workdir: Path | None = None) -> dict[str, str]:
    """The child's environment: no proxy, telemetry diverted into the run."""
    env = {key: value for key, value in os.environ.items()
           if key not in ("ANTHROPIC_BASE_URL", "ANTHROPIC_CUSTOM_HEADERS",
                          "ANTHROPIC_MODEL")}
    telemetry = run_dir / "telemetry"
    telemetry.mkdir(parents=True, exist_ok=True)
    env["AGENT_EXPERIENCE_PENDING"] = str(telemetry / "experience-pending.jsonl")
    env["AGENT_EXPERIENCE_LEDGER"] = str(telemetry / "experience.jsonl")
    if workdir is not None:
        # Execution scenarios only, and the confinement goes *under* the
        # interpreter rather than in front of it. Measured 2026-08-17: a granted
        # `Bash(python3:*)` wrote outside its workdir in 3 probes of 3, which no
        # permission string can prevent, because python is a general
        # interpreter and a grant bounds the command rather than what it does.
        #
        # The shim is named `python3` and goes first on PATH so the session
        # types what it would have typed anyway — the grant string, the
        # transcript and the `commands_run` audit all stay byte-identical to
        # the runs already in `runs/`. Confining the interpreter must not turn
        # into a second, unrecorded change to what the scenario measures.
        env["PATH"] = f"{HERE / 'sandbox'}:{env.get('PATH', '')}"
        env["REPLAY_WORKDIR"] = str(workdir)
    return env


def allowed_tools(execute: bool = False) -> list[str]:
    """Two grants, each one closing a hole the first pilot opened up.

    `acceptEdits` approves edits in the workdir and the simplest shell reads,
    and denies everything else — which in the 2026-08-12 r3 pilot meant the
    session could load `baton-dispatch` but not read its reference file, and
    could stage two dispatches but not log either outcome. Left alone, this
    harness would have graded criterion 3 on its own permission list rather
    than on the session's bookkeeping: s11's `b1` mistake, pointing the other
    way. Both grants are narrow, and the ledger writes land in the run's own
    diverted telemetry, not the machine's.
    """
    home = Path.home()
    ledger = ".agents/skills/experience-ledger/scripts/experience-log"
    grants = [f"Read(//{home}/.claude/skills/**)",
              f"Read(//{home}/.agents/skills/**)",
              f"Bash({home}/{ledger}:*)",
              f"Bash(~/{ledger}:*)"]
    if execute:
        # Opt-in, per scenario, and never on by default. Every batch run before
        # 2026-08-16 was measured with the four grants above, and a harness that
        # quietly widened them would make new runs incomparable to old ones
        # without anything in a `meta.json` saying so.
        #
        # What this grant is worth was measured on 2026-08-17 with
        # `permission-probe.sh`, and the first answer was wrong. The claim in
        # this file's history was that a compound command smuggles its tail past
        # the matcher. It does not: with *no* Bash grant at all, `acceptEdits`
        # already approves `touch` and `rm` inside the workdir on its own, so
        # the `rm -rf __pycache__` seen riding a `v1` pilot's `python3 ...;` was
        # that, not a matcher bug. Withhold this grant and `python3` is blocked
        # outright, so the opt-in is real.
        #
        # The hole was elsewhere and larger: a granted `python3` wrote a file
        # outside its workdir in 3 probes of 3. No permission string fixes that,
        # because a grant bounds which command runs and python is a general
        # interpreter. So the containment sits *under* the interpreter — see
        # `child_env`, which puts a sandboxed `python3` first on the child's
        # PATH. Re-measured after: writing outside is denied, child processes
        # included, and a real `v2` run still delivers 10/10.
        grants.append("Bash(python3:*)")
        # `Bash(sh:*)` added 2026-08-17, and the shim under it in the same change.
        #
        # Two cells ship shell fixtures — `e1`'s `launch.sh`, `e2`'s `check.sh` —
        # and the grant above never let either run. Measured with `sh-probe.sh`:
        # under the python-only grant, `./x.sh`, `sh x.sh` and a PATH-resolved
        # shebang were all denied, 0 of 2 each. So `e1` could not be passed at
        # all (its expectation needs a real restart) and `e2` could only be
        # passed by editing a check nobody was allowed to run — which is the one
        # thing `test-first-change` forbids, and five of five sessions with that
        # skill loaded refused and said why.
        #
        # Granting it bare reproduces the python hole one interpreter over: with
        # `Bash(sh:*)` and no shim, `sh escape.sh` wrote outside the workdir in 2
        # probes of 2. With `sandbox/sh` first on PATH, the same probe runs 2 of 2
        # and escapes 0 of 2. Containment under the interpreter, not in front of
        # it, exactly as for `python3`.
        #
        # `./x.sh` stays denied: the matcher keys on the leading token, so it
        # would need its own grant, and the session can reach the same script
        # through `sh x.sh`. One working idiom is enough, and it is the one the
        # transcripts already reach for.
        grants.append("Bash(sh:*)")
    return grants


def commands_executed(events: Path) -> list[str]:
    """The commands that actually ran, denials removed.

    `commands_run` reads `tool_use` blocks, which are *requests*. A denied
    command appears there exactly like an approved one — measured 2026-08-17,
    when a `v3` pilot asked twice for `/usr/bin/python3`, was refused both
    times, and retried with the bare name. Both refusals were sitting in that
    run's audit looking like execution.

    It changed nothing this time: recomputed over the whole `v2` batch, the
    published 13/20 and 12/20 hold either way, because every run that had a
    denial also had an approved command doing the same job. That is luck, not
    design, and a measure that survives by luck is one bad batch from being
    wrong. Both lists are recorded so the difference stays visible.
    """
    ran, denied = [], set()
    for line in events.read_text(encoding="utf-8").splitlines():
        if '"tool_result"' not in line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        message = record.get("message")
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        for block in content if isinstance(content, list) else []:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                text = str(block.get("content"))
                if "requires approval" in text or "permission denied" in text.lower():
                    denied.add(block.get("tool_use_id"))
    for line in events.read_text(encoding="utf-8").splitlines():
        if '"Bash"' not in line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        message = record.get("message")
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        for block in content if isinstance(content, list) else []:
            if (isinstance(block, dict) and block.get("type") == "tool_use"
                    and block.get("name") == "Bash"
                    and block.get("id") not in denied):
                command = (block.get("input") or {}).get("command")
                if command:
                    ran.append(command)
    return ran


def commands_run(events: Path) -> list[str]:
    """Every shell line the session issued, read back out of its own stream.

    The execution grant is opt-in and narrow, but "narrow" is a claim about the
    allowlist and this is the observation. A reader who wants to know whether a
    `v1` run stayed inside its workdir does not have to trust the permission
    string — the commands are here, in the order they were approved.
    """
    seen: list[str] = []
    for line in events.read_text(encoding="utf-8").splitlines():
        if '"Bash"' not in line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        message = record.get("message")
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        for block in content if isinstance(content, list) else []:
            if (isinstance(block, dict) and block.get("type") == "tool_use"
                    and block.get("name") == "Bash"):
                command = (block.get("input") or {}).get("command")
                if command:
                    seen.append(command)
    return seen


def argv_for(prompt: str, session: str, first: bool,
             inject: str | None = None, execute: bool = False) -> list[str]:
    argv = ["claude", "--print", prompt,
            "--output-format", "stream-json", "--verbose",
            "--permission-mode", "acceptEdits",
            "--allowedTools", *allowed_tools(execute),
            "--strict-mcp-config"]
    if inject:
        # The client's own instructions arrive in the system prompt, and the
        # user contract arrives as user context. `--append-system-prompt` is the
        # closest thing this harness has to the first position — an
        # approximation, declared as one in the README, not an equivalence.
        argv += ["--append-system-prompt", inject]
    argv += ["--session-id", session] if first else ["--resume", session]
    return argv


def run_turn(prompt: str, session: str, first: bool, workdir: Path,
             env: dict[str, str], interrupt_after: float | None,
             inject: str | None = None, execute: bool = False) -> dict:
    """One turn. Returns what happened, including whether it was cut short."""
    proc = subprocess.Popen(argv_for(prompt, session, first, inject, execute),
                            cwd=workdir,
                            env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    interrupted = False
    try:
        out, err = proc.communicate(timeout=interrupt_after or TURN_TIMEOUT)
    except subprocess.TimeoutExpired:
        if interrupt_after is None:
            proc.kill()
            out, err = proc.communicate()
            return {"exit": proc.returncode, "stdout": out.decode(errors="replace"),
                    "stderr": "turn exceeded TURN_TIMEOUT", "interrupted": False,
                    "timed_out": True}
        # SIGINT first: the interrupt under test is a user stopping a run, not
        # a process being shot. SIGKILL is the fallback so a wedged child
        # cannot hang the harness.
        proc.send_signal(signal.SIGINT)
        try:
            out, err = proc.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            out, err = proc.communicate()
        interrupted = True
    return {"exit": proc.returncode, "stdout": out.decode(errors="replace"),
            "stderr": err.decode(errors="replace")[-2000:],
            "interrupted": interrupted, "timed_out": False}


def session_environment(stdout: str) -> dict[str, object]:
    """What the run actually had, read back out of its own event stream.

    s11 was confused four times by asking for a condition and getting a
    different one, so the condition is recorded from the run's own output
    rather than from the flags this script believes it passed.
    """
    servers, tools = None, None
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event.get("mcp_servers"), list):
            servers = [{"name": entry.get("name"), "status": entry.get("status")}
                       for entry in event["mcp_servers"]]
        if event.get("type") == "system" and isinstance(event.get("tools"), list):
            tools = event["tools"]
    return {"mcp_servers_in_session": servers,
            "tool_count_in_session": len(tools) if tools is not None else None}


def truncate_apply_log(workdir: Path, lines: int) -> dict[str, object]:
    """Drop the last `lines` entries of applied.log, as a killed write would.

    This is the part of r1 that makes "no duplicate writes" decidable instead
    of merely absent. After an interrupt the session still remembers what it
    reported doing; the disk does not agree. A run that resumes from its own
    memory leaves a hole exactly here, and a run that reconciles against the
    file does not. Both outcomes are visible in one artifact.
    """
    log = workdir / "applied.log"
    if not log.exists():
        return {"applied": False, "reason": "applied.log absent"}
    kept = [line for line in log.read_text(encoding="utf-8").splitlines() if line]
    dropped = kept[-lines:] if lines else []
    log.write_text("".join(f"{line}\n" for line in kept[:len(kept) - lines]),
                   encoding="utf-8")
    return {"applied": True, "before": len(kept), "after": len(kept) - lines,
            "dropped": dropped}


def preflight(clause: str, arm: str, workdir: Path, env: dict[str, str]) -> dict:
    """Ask the model whether the manipulation landed, before spending the run.

    An arm is only meaningful if the clause really left the agent's context, and
    the file having changed is not the same claim. s11 was confused four times
    by asking for a condition and measuring a different one.
    """
    asked = []
    for question, expected in contract_probes(clause, arm):
        done = subprocess.run(
            ["claude", "--print", question,
             "--output-format", "text", "--permission-mode", "manual",
             "--strict-mcp-config"],
            cwd=workdir, env=env, capture_output=True, text=True, timeout=300)
        out = done.stdout
        answer = ("YES" if re.search(r"\bYES\b", out, re.I)
                  else "NO" if re.search(r"\bNO\b", out, re.I) else "?")
        asked.append({"expected": expected, "answer": answer,
                      "landed": answer == expected})
    return {"probe": "manipulation-check", "clause": clause, "arm": arm,
            "asked": asked, "landed": all(row["landed"] for row in asked)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path,
                        help="directory for events, snapshots and meta.json")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the plan and the conditions, run nothing")
    parser.add_argument("--arm", choices=("a", "b", "c", "s", "w"), default="a",
                        help="a: contract as shipped (no swap). b: the load "
                             "instruction removed. c: every mention removed")
    parser.add_argument("--clause", default="baton-dispatch",
                        help="which contract clause the arm operates on")
    parser.add_argument("--preflight", action="store_true",
                        help="ask the model whether the manipulation landed, "
                             "before spending the run")
    args = parser.parse_args()

    spec, turns = parse_scenario(args.scenario)
    interrupt_turn = int(spec.get("interrupt_turn", 0))
    interrupt_after = float(spec.get("interrupt_after_secs", 0)) or None
    truncate = int(spec.get("truncate_after_interrupt", 0))

    if args.dry_run:
        print(json.dumps({
            "scenario": spec["id"], "turns": len(turns),
            "interrupt_turn": interrupt_turn or None,
            "interrupt_after_secs": interrupt_after,
            "truncate_after_interrupt": truncate or None,
            "marker": spec["marker"], "recovery_point": spec["recovery_point"],
            "expect": spec["expect"],
            "deployed_contract": sha(DEPLOYED)[:12] if DEPLOYED.exists() else None,
            "matches_repo_source": DEPLOYED.exists() and sha(DEPLOYED) == sha(SOURCE),
        }, indent=2, ensure_ascii=False))
        return 0

    run_dir = args.out.resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    env = child_env(run_dir)
    session = str(uuid.uuid4())

    # `/tmp` explicitly: outside ~/.claude, where a write is refused outright,
    # and outside the repo, whose project settings and CLAUDE.md would
    # otherwise join the construct. It is also the location the 2026-08-12
    # probes ran in, so it is the one known to be writable rather than the one
    # assumed to be.
    work = Path(tempfile.mkdtemp(prefix="replay-", dir="/tmp"))
    built = build_fixture(spec["fixture"], work)
    if str(spec.get("allow_execution", "")).lower() == "true":
        env = child_env(run_dir, work)

    stale = drifted()
    drift = bool(stale)
    if drift:
        print("WARNING: the deployed copy differs from repo source for "
              + ", ".join(stale) + "; this run's surface fingerprint will not "
              "describe what the agent read", file=sys.stderr)

    with contract_arm(args.clause, args.arm) as arm_state:
        if args.preflight:
            checked = preflight(args.clause, args.arm, work, env)
            print(json.dumps(checked, indent=2), file=sys.stderr)
            if not checked["landed"]:
                shutil.rmtree(work, ignore_errors=True)
                # Every probe, not the first: two-sided arms ask two questions
                # and the informative part is *which* of them missed. The old
                # message read one flat `answer` field, which stopped existing
                # when arms went two-sided — so the guard refused the run
                # correctly and then died formatting the reason, which is the
                # one moment the reason is worth having.
                missed = ", ".join(
                    f"answered {asked.get('answer')!r} where {asked.get('expected')!r}"
                    " was expected"
                    for asked in checked.get("asked", [])
                    if not asked.get("landed"))
                raise SystemExit(
                    f"manipulation did not land on arm {args.arm}: "
                    f"{missed or checked}. A run whose arm did not reach the "
                    "agent is not a data point.")
            arm_state["preflight"] = checked

        events = run_dir / "events.jsonl"
        events.write_text("", encoding="utf-8")
        records: list[dict] = []
        interrupt_state: dict[str, object] = {}

        for index, prompt in enumerate(turns, start=1):
            cut = interrupt_after if index == interrupt_turn else None
            result = run_turn(prompt, session, index == 1, work, env, cut,
                          spec.get("inject_system"),
                          str(spec.get("allow_execution", "")).lower() == "true")
            with events.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"replay_turn": index,
                                         "interrupted": result["interrupted"]}) + "\n")
                handle.write(result["stdout"])
                if not result["stdout"].endswith("\n"):
                    handle.write("\n")
            records.append({"turn": index, "exit": result["exit"],
                            "interrupted": result["interrupted"],
                            "timed_out": result["timed_out"],
                            "stderr_tail": result["stderr"][-400:],
                            **session_environment(result["stdout"])})
            print(f"turn {index}: exit {result['exit']}"
                  f"{' (interrupted)' if result['interrupted'] else ''}",
                  file=sys.stderr)

            # Snapshot every turn, not just the last. r2 asks when a per-turn
            # obligation first lapses, and that question cannot be answered from a
            # single final state. For the interrupted turn this snapshot is taken
            # before the truncation below, so the grader can see what the run had
            # actually written at the moment it was cut off.
            snapshot = run_dir / "snapshots" / f"turn-{index}"
            shutil.rmtree(snapshot, ignore_errors=True)
            shutil.copytree(work, snapshot)

            if index == interrupt_turn:
                interrupt_state = {"snapshot": f"snapshots/turn-{index}"}
                if truncate:
                    interrupt_state["truncation"] = truncate_apply_log(work, truncate)

    # What the session actually said, per turn, in a file small enough to keep.
    #
    # The event stream and the transcript are ignored on purpose - large,
    # machine-specific, and for the questions this harness was built to answer
    # meta.json really was everything a reader needed. That stopped being true
    # on 2026-08-28: gate_lines.distance scores how far a mandated line sits
    # from its template, and the condition attached to it was to rescore seeds
    # already run. Nothing could be rescored, because the only durable record
    # of a run held the conditions and the verdict but never the reply.
    #
    # So this extracts the one thing a rescore reads rather than un-ignoring
    # the stream. final_text comes from grade.py so the retained text is
    # byte-identical to what grading saw; a second parser here would be free to
    # drift from the first, and the drift would be invisible.
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from grade import final_text
    finally:
        sys.path.pop(0)
    replies = ["# Replies, one section per turn",
               "",
               "Extracted at run time by `run.py` via `grade.py`'s `final_text`.",
               "Kept because a rescore of the gate lines needs what was said,",
               "and `meta.json` records only the conditions and the verdict.",
               ""]
    # Parsed once, outside the loop: the stream is the large file this whole
    # comment is about, and re-reading it per turn would be one full parse of
    # it for every turn in the run.
    #
    # Unparseable lines are skipped rather than raised on. The stream is the
    # agent's own stdout, so a reply that happens to begin a line with "{" puts
    # a non-JSON line in here, and a hard parse would abort the write *after*
    # the run finished - losing the whole run to a formatting accident in its
    # own output, which is the one failure this file exists to prevent.
    stream = []
    for line in events.read_text(encoding="utf-8").splitlines():
        if not line.strip().startswith("{"):
            continue
        try:
            stream.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    for record in records:
        turn = record["turn"]
        start = next((i for i, event in enumerate(stream)
                      if event.get("replay_turn") == turn), None)
        end = next((i for i, event in enumerate(stream)
                    if event.get("replay_turn") == turn + 1), len(stream))
        said = final_text(stream[start:end]) if start is not None else ""
        replies += [f"## Turn {turn}", "", "```text", said.rstrip() or
                    "(no result payload; see events.jsonl)", "```", ""]
    (run_dir / "replies.md").write_text("\n".join(replies), encoding="utf-8")

    final = run_dir / "workdir"
    shutil.rmtree(final, ignore_errors=True)
    shutil.copytree(work, final)
    shutil.rmtree(work, ignore_errors=True)

    # What the leaves did is in neither the `--print` stream nor the session
    # transcript: the r3 pilot's stream held 176 events and its transcript 63
    # records, both with zero sidechain rows. Each leaf gets its own file under
    # `<session>/subagents/`. All of it lives in `~/.claude/projects`, which is
    # machine state rather than a retained artifact, so it is copied in and
    # criterion 4 holds for the leaf half too.
    for found in sorted((Path.home() / ".claude" / "projects")
                        .glob(f"*/{session}.jsonl")):
        shutil.copy2(found, run_dir / "transcript.jsonl")
        leaves = found.with_suffix("") / "subagents"
        if leaves.is_dir():
            target = run_dir / "subagents"
            shutil.rmtree(target, ignore_errors=True)
            shutil.copytree(leaves, target)
        break

    (run_dir / "meta.json").write_text(json.dumps({
        "scenario": args.scenario.name,
        "id": spec["id"],
        "measures": spec.get("measures"),
        "marker": spec["marker"],
        "recovery_point": spec["recovery_point"],
        "expect": spec["expect"],
        "session": session,
        # Both halves, deliberately: `fixture` is the builder the scenario asked
        # for and `fixture_files` is what that builder actually produced. Keeping
        # only the second identifies the builder by its output, which is fine
        # until an output changes; keeping both is how a run says what it
        # requested as well as what it got.
        "fixture": spec.get("fixture"),
        "fixture_files": built,
        "turns": records,
        "interrupt": interrupt_state,
        "surface": surface_fingerprint(),
        "allow_execution": str(spec.get("allow_execution", "")).lower() == "true",
        # The boolean alone cannot say what an execution grant meant on the day,
        # and the grant set has already changed once. The list travels with the
        # run so old and new stay comparable.
        "resident_skills": resident_skills(),
        "granted_tools": allowed_tools(
            str(spec.get("allow_execution", "")).lower() == "true"),
        "commands_run": commands_run(events),
        "commands_executed": commands_executed(events),
        "deployed_contract_sha256": sha(DEPLOYED) if DEPLOYED.exists() else None,
        "matches_repo_source": not drift,
        "arm": arm_state,
        "target": spec.get("target"),
        "contract_rule": spec.get("contract_rule"),
        "inject_system": spec.get("inject_system"),
        "expect_skill": spec.get("expect_skill"),
        # Carried since 2026-08-17. `grade_e5` branches on it to decide which of
        # the paired authority arms it is grading, and without it every run read
        # None and graded as the fix arm - so the diagnose arm's correct
        # do-nothing run scored incorrect. The pair only means anything when each
        # side is graded by its own criterion.
        "expect_authority": spec.get("expect_authority"),
        "hooks": "live (user settings source; not suppressible without also "
                 "dropping the contract)",
        "telemetry_diverted_to": str(run_dir / "telemetry"),
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"run kept at {run_dir}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
