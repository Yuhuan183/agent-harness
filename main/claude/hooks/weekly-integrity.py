#!/usr/bin/env python3
"""Weekly-throttled integrity check, run from SessionStart.

Deterministic checks only: manifest parity between the source checkout and every
deployed HOME target, routing pin/alias/prior freshness, delegation alarms, and
ledger reconciliation. A git-managed ~/.claude additionally reports uncommitted
changes, which is a supplement to parity and never a substitute for it.
Findings and check failures are printed to stdout for the active session.
The hook is fail-open, but its throttle advances only after the checks complete.
"""
import json
import os
import subprocess
import sys
import time

PERIOD = 7 * 86400
STAMP = os.path.expanduser("~/.claude/telemetry/.integrity-last-run")

# The SessionStart hook registration allows 60 s. Per-subprocess timeouts alone
# cannot honour that: a drift-heavy run chains one 30 s parity check, two 15 s
# merge verifications and several 10 s resolver checks, and the host kills the
# hook before it prints findings or writes its stamp — so it silently retries
# every session, never completing. One monotonic deadline caps the whole run;
# each subprocess takes the smaller of its own cap and the time left, so an
# overrun surfaces as a normal timeout finding with output preserved.
BUDGET = 50.0
_deadline = time.monotonic() + BUDGET


def budget(cap):
    """Seconds for the next subprocess: its own cap, or whatever time is left."""
    return max(1.0, min(cap, _deadline - time.monotonic()))


def resolve_harness_repo():
    """Resolve the authoritative checkout from env, deployment marker, or fallback."""
    configured = os.environ.get("AGENT_HARNESS_REPO")
    if configured:
        return os.path.expanduser(configured)
    marker = os.path.expanduser("~/.agents/skills/.agent-harness-source")
    try:
        with open(marker, encoding="utf-8") as stream:
            marked = stream.readline().strip()
    except OSError:
        marked = ""
    return os.path.expanduser(marked or "~/WorkSpace/agent-harness")


def load_deployment_inventory():
    """HOME-relative paths sync.sh last deployed, grouped by target root.

    Absent or unreadable means unknown, never "nothing is ours": a missing
    inventory costs a retired-file finding, and inventing ownership from the
    directory listing is exactly the error this replaced.
    """
    inventory = {}
    try:
        with open(os.path.expanduser("~/.agents/.deployed-files.tsv"),
                  encoding="utf-8") as stream:
            for line in stream:
                root, _, rel = line.rstrip("\n").partition("\t")
                if root and rel:
                    inventory.setdefault(root, []).append(rel)
    except OSError:
        pass
    return inventory


def load_deployment_manifest(repo):
    """Return validated repo-relative source, HOME-relative target, and mode."""
    path = os.path.join(repo, "scripts", "deployment-manifest.tsv")
    pairs = []
    sources = set()
    targets = set()
    with open(path, encoding="utf-8") as manifest:
        for line_number, raw in enumerate(manifest, 1):
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            fields = line.split("\t")
            if len(fields) not in (2, 3) or not all(fields):
                raise ValueError(f"malformed deployment manifest line {line_number}")
            source, target = fields[:2]
            mode = fields[2] if len(fields) == 3 else ""
            if mode not in ("", "merge", "merge-json", "merge-toml"):
                raise ValueError(f"invalid deployment mode on line {line_number}")
            restricted = {
                "merge": ("main/.agents/skills", ".agents/skills"),
                "merge-json": ("main/claude/settings.json", ".claude/settings.json"),
                "merge-toml": ("main/codex/config.merge.toml", ".codex/config.toml"),
            }
            if mode in restricted and (source, target) != restricted[mode]:
                raise ValueError(
                    f"{mode} mode is restricted to its declared mapping on line {line_number}"
                )
            source_prefixes = ("main/.agents/", "main/claude/", "main/codex/")
            target_prefixes = (".agents/", ".claude/", ".codex/")
            if not source.startswith(source_prefixes) or not target.startswith(target_prefixes):
                raise ValueError(f"unsafe deployment manifest line {line_number}")
            if any(part in ("", ".", "..") for part in source.split("/")) \
                    or any(part in ("", ".", "..") for part in target.split("/")):
                raise ValueError(f"unsafe deployment path line {line_number}")
            # Same rule as sync.sh's validate_manifest: a directory is rsync'd
            # into the target's parent, so a renaming directory row deploys to
            # the source's basename and the drift check below would compare the
            # wrong pair. Kept in step deliberately - this is a second
            # implementation of one schema, which is what the manifest test
            # below exists to catch.
            if not mode and os.path.isdir(os.path.join(repo, source)) \
                    and source.rsplit("/", 1)[-1] != target.rsplit("/", 1)[-1]:
                raise ValueError(
                    f"directory deployment renames its target on line {line_number}")
            if source in sources or target in targets:
                raise ValueError(f"duplicate deployment manifest line {line_number}")
            sources.add(source)
            targets.add(target)
            pairs.append((source, target, mode))
    if not pairs:
        raise ValueError("deployment manifest is empty")
    return pairs


def load_project_skill_names(root):
    """Validate and return the project-owned skills under a merged skill root."""
    inventory = os.path.join(root, "INSTALLED.txt")
    with open(inventory, encoding="utf-8") as stream:
        names = [line.rstrip("\n") for line in stream]
    if not names or any(not name for name in names) or len(names) != len(set(names)):
        raise ValueError("invalid project skill inventory")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-")
    for name in names:
        if set(name) - allowed or name.startswith("-") or name.endswith("-") or "--" in name:
            raise ValueError(f"invalid project skill name: {name}")
        if not os.path.isfile(os.path.join(root, name, "SKILL.md")):
            raise ValueError(f"listed project skill is missing SKILL.md: {name}")
    actual = {
        entry
        for entry in os.listdir(root)
        if os.path.isfile(os.path.join(root, entry, "SKILL.md"))
    }
    if actual != set(names):
        raise ValueError("project skill inventory does not match source directories")
    return names

try:
    if os.path.exists(STAMP) and time.time() - os.path.getmtime(STAMP) < PERIOD:
        sys.exit(0)

    findings = []
    checks_completed = True
    claude_dir = os.path.expanduser("~/.claude")
    # ~/.claude is normally populated by scripts/sync.sh rsync from the harness
    # repo, not a git checkout. Every manifest target is compared via an rsync
    # dry-run against the source checkout (the same paths sync.sh manages).
    harness_repo = resolve_harness_repo()
    try:
        # A git-managed ~/.claude gets one *extra* check, not a substitute one.
        # `git status` answers "does this checkout match its own HEAD", which
        # is silent when the checkout is clean but pinned to an old commit —
        # exactly the stale deployment this hook exists to notice. So it
        # reports uncommitted changes only, and manifest parity still runs for
        # the .claude targets (2026-07-28).
        claude_git_managed = os.path.isdir(os.path.join(claude_dir, ".git"))
        if claude_git_managed:
            r = subprocess.run(
                ["git", "-C", claude_dir, "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=budget(10),
            )
            if r.returncode != 0:
                checks_completed = False
                detail = (r.stderr or r.stdout).rstrip()
                findings.append(
                    f"contract-repo check failed (exit {r.returncode}):\n{detail}"
                )
            elif r.stdout.strip():
                findings.append(
                    "contract-repo drift (uncommitted changes in ~/.claude):\n"
                    + r.stdout.rstrip()
                )
        if not os.path.isdir(os.path.join(harness_repo, "main", "claude")):
            # A managed deployment without a reachable source checkout has no
            # manifest drift monitoring — that is a finding, not a silent skip,
            # and the throttle must not advance past it.
            checks_completed = False
            findings.append(
                "deployment drift check unavailable: harness checkout not found at "
                f"{harness_repo}; set AGENT_HARNESS_REPO to the source checkout "
                "(drift monitoring is suspended until then)"
            )
        else:
            drift = []
            home_dir = os.path.expanduser("~")
            inventory = load_deployment_inventory()
            for source_rel, target_rel, mode in load_deployment_manifest(harness_repo):
                src = os.path.join(harness_repo, source_rel)
                if not os.path.lexists(src):
                    raise ValueError(f"deployment source missing: {source_rel}")
                deployed = os.path.join(os.path.expanduser("~"), target_rel)
                if mode in ("merge-json", "merge-toml"):
                    merger = ("merge-settings.py" if mode == "merge-json"
                              else "merge-toml.py")
                    # A merged target legitimately carries machine keys and
                    # foreign hooks the source lacks, so byte comparison would
                    # report drift forever and train the reader to ignore it.
                    # The real invariant is that re-merging changes nothing.
                    verify = subprocess.run(
                        [sys.executable,
                         os.path.join(harness_repo, "scripts", merger),
                         src, deployed, "--verify"],
                        capture_output=True, text=True, timeout=budget(15),
                    )
                    if verify.returncode != 0:
                        drift.append(
                            f"~/{target_rel}: repo-declared content not present "
                            f"(run scripts/sync.sh --apply)"
                        )
                    continue
                checks = [(src, deployed, target_rel)]
                if mode == "merge":
                    checks = [
                        (
                            os.path.join(src, name),
                            os.path.join(deployed, name),
                            f"{target_rel}/{name}",
                        )
                        for name in load_project_skill_names(src)
                    ]
                    checks.append((
                        os.path.join(src, "INSTALLED.txt"),
                        os.path.join(deployed, "INSTALLED.txt"),
                        f"{target_rel}/INSTALLED.txt",
                    ))
                for check_src, check_deployed, check_target_rel in checks:
                    if os.path.isdir(check_src):
                        r = subprocess.run(
                            # Deliberately NOT --delete-excluded. This is a
                            # read-only comparison, and the excluded patterns
                            # are bytecode the deployed scripts regenerate as
                            # they run. Counting those as drift produced an
                            # alarm that could never clear, which is worse than
                            # no alarm: it trains the reader to skip the real one.
                            # --delete only where the whole directory is this
                            # repo's (a merge-mode skill). A plain target such
                            # as ~/.claude/hooks is a shared namespace, and
                            # --delete there reported a third-party installer's
                            # file as our drift; retired files are found from
                            # the deployment inventory instead (2026-07-29).
                            ["rsync", "-a", "--checksum", "--links"]
                            + (["--delete"] if mode == "merge" else [])
                            + ["--exclude", "__pycache__/", "--exclude", "*.pyc",
                               "--exclude", ".DS_Store", "-n", "--itemize-changes",
                               check_src, os.path.dirname(check_deployed) + "/"],
                            capture_output=True, text=True, timeout=budget(30),
                        )
                    else:
                        same = subprocess.run(
                            ["cmp", "-s", check_src, check_deployed], timeout=budget(10),
                        )
                        r = subprocess.CompletedProcess(
                            args=same.args, returncode=0,
                            stdout="" if same.returncode == 0 else "file content differs\n",
                            stderr="",
                        )
                    if r.returncode != 0:
                        checks_completed = False
                        detail = (r.stderr or r.stdout).rstrip()
                        findings.append(
                            f"deployment drift check failed (rsync exit {r.returncode}, "
                            f"{check_target_rel}):\n{detail}"
                        )
                        break
                    for line in r.stdout.splitlines():
                        # rsync -n itemized lines starting with '.' are unchanged;
                        # anything else means content would be copied (drift).
                        if line and not line.startswith(".") and not line.endswith("/"):
                            drift.append(f"~/{check_target_rel}: {line}")
                if not checks_completed:
                    break
                # The other half of what --delete used to cover, without its
                # ownership error: a file this repo deployed before and no
                # longer ships is drift; one it never deployed is not ours.
                if mode == "" and os.path.isdir(src):
                    for rel in inventory.get(target_rel, ()):
                        source_path = os.path.join(
                            src, os.path.relpath(rel, target_rel))
                        if (not os.path.lexists(source_path)
                                and os.path.lexists(
                                    os.path.join(home_dir, rel))):
                            drift.append(
                                f"~/{rel}: deployed file the repo no longer "
                                "ships (run scripts/sync.sh --apply)")
            if drift:
                findings.append(
                    "deployment drift (managed HOME targets differ from repo — "
                    "run scripts/sync.sh --apply or commit repo changes):\n"
                    + "\n".join(drift)
                )
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        checks_completed = False
        findings.append(f"contract-repo check failed: {exc}")

    try:
        rep = subprocess.run(
            [os.path.join(claude_dir, "scripts", "delegation-report"), "--days", "7"],
            capture_output=True,
            text=True,
            timeout=budget(10),
        )
        if rep.returncode == 1:
            findings.append("delegation audit alarm:\n" + rep.stdout.rstrip())
        elif rep.returncode != 0:
            checks_completed = False
            detail = (rep.stderr or rep.stdout).rstrip()
            findings.append(f"delegation audit failed (exit {rep.returncode}):\n{detail}")
    except (OSError, subprocess.TimeoutExpired) as exc:
        checks_completed = False
        findings.append(f"delegation audit failed: {exc}")

    # A deployment without the resolver (e.g. a partially synced ~/.claude)
    # cannot run the pin-drift check; that is incomplete coverage, never a
    # silent skip — report it and withhold the throttle stamp.
    routing_script = os.path.join(claude_dir, "scripts", "model-routing")
    try:
        if not os.access(routing_script, os.X_OK):
            pins = None
            checks_completed = False
            findings.append(
                f"model-routing resolver unavailable at {routing_script}; "
                "pin-drift check not run"
            )
        else:
            pins = subprocess.run(
                [routing_script, "check-pins"],
                capture_output=True,
                text=True,
                timeout=budget(10),
            )
        if pins is None:
            pass
        elif pins.returncode == 1:
            findings.append(
                "model-routing pin drift:\n" + (pins.stderr or pins.stdout).rstrip()
            )
        elif pins.returncode != 0:
            checks_completed = False
            detail = (pins.stderr or pins.stdout).rstrip()
            findings.append(f"model-routing check failed (exit {pins.returncode}):\n{detail}")
    except (OSError, subprocess.TimeoutExpired) as exc:
        checks_completed = False
        findings.append(f"model-routing check failed: {exc}")

    # A frontmatter pin buys whatever the CLI currently calls `opus`; the config
    # only asserts which generation that is. experience-log seeds the ledger's
    # model field from the route, so an unnoticed generation move files every
    # dispatch under a model that never ran. Nothing else catches that.
    try:
        # A missing resolver is already a finding from the pin-drift block
        # above, which also withheld the stamp; do not report it twice.
        if os.access(routing_script, os.X_OK):
            aliases = subprocess.run(
                [routing_script, "check-aliases"],
                capture_output=True,
                text=True,
                timeout=budget(10),
            )
            if aliases.returncode == 1:
                findings.append(
                    "model-routing alias drift:\n"
                    + (aliases.stderr or aliases.stdout).rstrip()
                )
            elif aliases.returncode != 0:
                checks_completed = False
                detail = (aliases.stderr or aliases.stdout).rstrip()
                findings.append(
                    f"model-routing alias check failed (exit {aliases.returncode}):\n{detail}"
                )
    except (OSError, subprocess.TimeoutExpired) as exc:
        checks_completed = False
        findings.append(f"model-routing alias check failed: {exc}")

    codex_routing = os.path.expanduser("~/.codex/scripts/model-routing")
    # Return code only. `validate` also prints WARNING lines for a quality
    # floor whose approved routes have no measured score, or whose tier minima
    # do not separate — deliberately not relayed here. That state changes only
    # when someone edits a routing file, and `scripts/sync.sh` preflight is the
    # gate every such edit passes through, so the warnings are surfaced at the
    # moment they can be acted on. A weekly repeat would be a standing alarm
    # for a condition nobody is being asked to fix this week, which is the
    # failure mode described in the reconciliation note below (2026-07-30
    # review: the warnings really were invisible, but the missing surface was
    # the deploy path, not this one).
    try:
        if not os.access(codex_routing, os.X_OK):
            checks_completed = False
            findings.append(
                f"Codex model-routing resolver unavailable at {codex_routing}; "
                "validation not run"
            )
        else:
            validated = subprocess.run(
                [codex_routing, "validate"], capture_output=True, text=True, timeout=budget(10)
            )
            if validated.returncode != 0:
                checks_completed = False
                detail = (validated.stderr or validated.stdout).rstrip()
                findings.append(
                    f"Codex model-routing check failed (exit {validated.returncode}):\n"
                    f"{detail}"
                )
    except (OSError, subprocess.TimeoutExpired) as exc:
        checks_completed = False
        findings.append(f"Codex model-routing check failed: {exc}")

    # `prior_review` says to re-audit the benchmark priors 90 days after as_of,
    # but a cadence stated only in prose, inside the config it governs, is a
    # note nobody is scheduled to read: as_of ages silently while the routes go
    # on citing it as current evidence. This is that scheduled reader. It
    # alarms without withholding the stamp, like pin drift — the finding
    # recurs weekly until someone re-audits and moves as_of.
    for label, resolver in (("Claude", routing_script), ("Codex", codex_routing)):
        try:
            if not os.access(resolver, os.X_OK):
                continue  # an unavailable resolver is already a finding above
            priors = subprocess.run(
                [resolver, "check-priors"], capture_output=True, text=True, timeout=budget(10)
            )
            if priors.returncode == 1:
                findings.append(
                    "benchmark priors overdue:\n"
                    + (priors.stderr or priors.stdout).rstrip()
                )
            elif priors.returncode != 0:
                checks_completed = False
                detail = (priors.stderr or priors.stdout).rstrip()
                findings.append(
                    f"{label} prior-review check failed "
                    f"(exit {priors.returncode}):\n{detail}"
                )
        except (OSError, subprocess.TimeoutExpired) as exc:
            checks_completed = False
            findings.append(f"{label} prior-review check failed: {exc}")

    # Informational only: surface dispatch-experience hints or a missing-data
    # warning. Best-effort — a failure here neither blocks the throttle nor alarms.
    #
    # Read the machine output, not the human table: a cohort exists per role x
    # task class, so most of them sit below the comparable-n threshold at any
    # time and their "keep collecting" hints would put this check permanently in
    # alarm — which is worse than no alarm, because it trains the reader to skip
    # the real one. Those cohorts are named in `hints_insufficient` and dropped
    # here; "log every dispatch" is already the standing contract instruction.
    # An empty ledger is different: it means the log loop is not running at all,
    # and it clears after the first logged dispatch.
    try:
        exp = subprocess.run(
            [os.path.expanduser(
                "~/.agents/skills/experience-ledger/scripts/experience-report"),
             "--json"],
            capture_output=True,
            text=True,
            timeout=budget(10),
        )
        report = json.loads(exp.stdout) if exp.returncode == 0 else {}
        insufficient = set(report.get("hints_insufficient") or ())
        actionable = [f"hint: {cohort:<28} {hint}"
                      for cohort, hint in sorted((report.get("hints") or {}).items())
                      if cohort not in insufficient]
        if actionable:
            findings.append("dispatch-experience hints:\n" + "\n".join(actionable))
        elif exp.returncode == 0 and not report.get("by_cohort_provider"):
            findings.append(
                "dispatch-experience gap: no reviewed outcomes in the configured window; "
                "log the next comparable dispatch after quality-check"
            )
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass

    # Informational: the contract requires logging every dispatch after QC, but
    # nothing else catches a forgotten log. A loggable SubagentStop stub still
    # sitting in the pending file a day later *may* be an un-reconciled dispatch.
    #
    # It is only un-reconciled if the ledger has no record for it. An earlier
    # version asked the pending file alone and reported every past dispatch
    # forever, including ones whose outcome was sitting in the ledger under the
    # same dispatch id; a permanent alarm is worse than none, because it trains
    # the reader to skip the real one.
    #
    # `experience-log` now clears the stub on any run that names a dispatch id,
    # so most reconciled stubs are simply gone by the time this runs (the
    # comment here used to say explicit flags left them behind — true until
    # 2026-07-30, corrected on review). The ledger read stays because clearing
    # is best-effort: `consume_pending` failures are swallowed, and a log run
    # that names no dispatch at all leaves the stub while filing a record this
    # loop cannot match to it. The residue is a false positive, never a missed
    # one, which is the safe direction for an informational alarm.
    #
    # Best-effort; never blocks the throttle.
    try:
        from datetime import datetime, timezone
        loggable_roles = {
            "explore", "mech-executor", "executor", "plan-verifier",
            "verifier", "security-reviewer", "security-executor",
        }
        ledger_path = os.environ.get(
            "AGENT_EXPERIENCE_LEDGER",
            os.path.expanduser("~/.agents/telemetry/experience.jsonl"),
        )
        reconciled = set()
        try:
            with open(ledger_path, encoding="utf-8") as stream:
                for raw in stream:
                    if not raw.strip():
                        continue
                    try:
                        logged = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    if logged.get("dispatch_id"):
                        reconciled.add(logged["dispatch_id"])
        except OSError:
            pass
        pending_path = os.environ.get(
            "AGENT_EXPERIENCE_PENDING",
            os.path.expanduser("~/.agents/telemetry/experience-pending.jsonl"),
        )
        cutoff = datetime.now(timezone.utc).timestamp() - 86400
        stale = {}
        with open(pending_path, encoding="utf-8") as stream:
            for raw in stream:
                if not raw.strip():
                    continue
                try:
                    row = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                agent_type = row.get("agent_type") or ""
                if row.get("event") == "SubagentStart":
                    # Native Codex has no completion hook, so its dispatches
                    # stage their own launch (`experience-stage`) and a
                    # forgotten outcome shows up as a launch nothing answered.
                    # Only that carrier qualifies: a hook-written start belongs
                    # to a dispatch whose own SubagentStop will report it.
                    if row.get("request_source") != "codex":
                        continue
                elif row.get("event") != "SubagentStop":
                    continue
                if agent_type not in loggable_roles and "codex" not in agent_type:
                    continue
                # A stub with no dispatch id predates the field and cannot be
                # reconciled by the command this finding recommends, which
                # requires `--dispatch-id`. The pending hook now always writes
                # one, so no new stub can land here.
                dispatch_id = row.get("dispatch_id")
                if not dispatch_id or dispatch_id in reconciled:
                    continue
                try:
                    ts = datetime.fromisoformat(row["ts"]).timestamp()
                except (KeyError, ValueError, TypeError):
                    continue
                # A staged native Codex dispatch has two rows; report the
                # dispatch once, dated from whichever row is older.
                if ts < cutoff:
                    stale[dispatch_id] = min(stale.get(dispatch_id, ts), ts)
        if stale:
            findings.append(
                "un-reconciled dispatches (launched or completed but never "
                "logged to the experience ledger; log with experience-log "
                "--from-pending --dispatch-id <id> --outcome <o>, or retire a "
                "native Codex launch that never ran with experience-stage "
                "--cancel):\n" + "\n".join(stale)
            )
    except OSError:
        pass

    # A gate that stopped being able to read its carrier stops gating, and the
    # only sign is a note on the stderr of one dispatch nobody re-reads.
    # verifier-quota counts consecutive dispatches whose payload carried no
    # `prompt_id` and clears the count the moment one does, so a standing count
    # means the field is gone (a CLI change), not absent once.
    try:
        with open(os.path.expanduser("~/.claude/telemetry/.verifier-quota.json"),
                  encoding="utf-8") as stream:
            misses = ((json.load(stream) or {}).get("_carrier") or {}).get("misses")
        if isinstance(misses, int) and misses >= 3:
            findings.append(
                f"verifier quota not enforceable: {misses} consecutive Agent "
                "dispatches carried no prompt_id, so the one-outcome-verifier "
                "budget has been allowing every dispatch. Check whether the "
                "CLI still sends prompt_id on hook payloads "
                "(main/claude/hooks/verifier-quota.py)"
            )
    except (OSError, ValueError, AttributeError):
        pass

    if checks_completed:
        try:
            os.makedirs(os.path.dirname(STAMP), exist_ok=True)
            with open(STAMP, "w", encoding="utf-8") as stamp:
                stamp.write(str(int(time.time())))
        except OSError as exc:
            findings.append(f"integrity throttle update failed: {exc}")

    if findings:
        print("[weekly-integrity] issues found — relay these to the user:")
        for f in findings:
            print(f)
except Exception as exc:
    print(f"[weekly-integrity] check failed unexpectedly: {exc}")
sys.exit(0)
