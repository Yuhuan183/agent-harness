#!/usr/bin/env python3
"""Weekly-throttled integrity check, run from SessionStart.

Deterministic checks only: manifest parity between the source checkout and every
deployed HOME target, routing pin/alias/prior freshness, delegation alarms, and
ledger reconciliation. A git-managed ~/.claude additionally reports uncommitted
changes, which is a supplement to parity and never a substitute for it.
Findings and check failures are printed to stdout for the active session.
The hook is fail-open, but its throttle advances only after the checks complete.
"""
import importlib.util
import json
import os
import re
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
# The smallest slice worth handing out. Below this a check reports a timeout
# instead of an answer, so there is nothing to buy by starting it.
MIN_SLICE = 1.0
_deadline = time.monotonic() + BUDGET


class DeadlineExhausted(Exception):
    """No time left inside BUDGET while checks are still pending."""


UNTIED_ID = re.compile(r"^[0-9a-fA-F-]{36}:\S+$")


def budget(cap):
    """Seconds for the next subprocess: its own cap, or whatever time is left.

    The floor here used to be unconditional (`max(1.0, ...)`), which made the
    deadline advisory rather than a cap: one run schedules 44 budget-governed
    subprocesses (38 driven by manifest rows, 6 fixed), and past the deadline
    every one of them still got its 1 s, so a drift-heavy run could reach ~94 s
    against a 60 s registration — the exact overrun the deadline was added to
    prevent (2026-08-02 review). Past the deadline there is no slice left to
    hand out, so scheduling stops here and the caller reports why.
    """
    left = _deadline - time.monotonic()
    if left < MIN_SLICE:
        raise DeadlineExhausted(
            f"integrity run hit its {BUDGET:.0f}s budget with checks still pending"
        )
    return min(cap, left)


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

def last_completed_run():
    """Epoch of the last completed run, from what the stamp *says*.

    The throttle used to read the stamp's mtime, which is metadata anyone can
    move without the run happening: a restore, an rsync or a touch makes an
    overdue audit look fresh, and the audit then skips itself with no signal.
    Observed on 2026-08-21 with a stamp whose content said 08-12 and whose mtime
    said 08-19 - nine days without a run, reported as two. The content is
    written only by a completed run (see the stamp write below), so it is the
    field that means what the throttle needs. mtime stays as the fallback for a
    stamp written before this change or corrupted since; a missing stamp reads
    as "never ran".
    """
    try:
        with open(STAMP, encoding="utf-8") as stream:
            return float(stream.read().strip())
    except (OSError, ValueError):
        pass
    try:
        return os.path.getmtime(STAMP)
    except OSError:
        return float("-inf")


def carrier_validated_on():
    """Runtime that leaf-redispatch records as having carried `agent_type`.

    Read from the sibling hook rather than duplicated here: one constant, and
    an operator who advances it edits the file the gate actually lives in.
    """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "leaf-redispatch.py")
    try:
        with open(path, encoding="utf-8") as stream:
            source = stream.read()
    except OSError:
        return None
    match = re.search(r"^CARRIER_VALIDATED_ON\s*=\s*\((\d+),\s*(\d+),\s*(\d+)\)",
                      source, re.MULTILINE)
    return tuple(map(int, match.groups())) if match else None


def live_runtime_version():
    """This machine's Claude Code version, or None when it cannot be read.

    Reuses runtime-guard's cached probe so an upgrade invalidates both at once;
    falls back to nothing rather than to a stale answer, because a wrong version
    here would silence the finding it is supposed to raise. The environment
    override exists only for deterministic tests.

    Scheduled through `budget()` like every other subprocess in this run. A warm
    cache answers in about a millisecond, but the cold path is a subprocess, and
    the cold path is exactly the one that follows a CLI upgrade - which is when
    this check has something to say. Skipping the deadline here would spend time
    it had already handed out, and silently: without `budget()` there is nothing
    to raise, so the overrun would not even be reported.
    """
    forced = os.environ.get("AGENT_RUNTIME_VERSION")
    if forced:
        # No subprocess, so nothing to schedule.
        match = re.search(r"\b(\d+)\.(\d+)\.(\d+)\b", forced)
        return tuple(map(int, match.groups())) if match else None
    slice_seconds = budget(5)
    guard = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "runtime-guard.py")
    try:
        spec = importlib.util.spec_from_file_location("runtime_guard", guard)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.parse_version(module.probe_version(slice_seconds))
    except Exception:  # noqa: BLE001 - an unreadable probe is "unknown", not a failure
        return None


# Held outside the run so that a run stopped part-way still reports what it
# managed to find. Losing the partial findings would make an overrun look like
# a clean session, which is the failure the budget exists to make visible.
findings = []
checks_completed = True

try:
    if time.time() - last_completed_run() < PERIOD:
        sys.exit(0)

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
            covered_roots = set()
            for source_rel, target_rel, mode in load_deployment_manifest(harness_repo):
                covered_roots.add(target_rel)
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
                # `merge` is included: a skill dropped from INSTALLED.txt leaves
                # a deployed tree that the per-skill comparison above never
                # visits, because that loop only walks the skills still listed.
                if mode in ("", "merge") and os.path.isdir(src):
                    for rel in inventory.get(target_rel, ()):
                        source_path = os.path.join(
                            src, os.path.relpath(rel, target_rel))
                        if (not os.path.lexists(source_path)
                                and os.path.lexists(
                                    os.path.join(home_dir, rel))):
                            drift.append(
                                f"~/{rel}: deployed file the repo no longer "
                                "ships (run scripts/sync.sh --apply)")
            # Roots the inventory still claims but no manifest row covers. Every
            # check above is keyed on a row that exists, so deleting a row made
            # its deployed tree invisible to this hook at the same moment it
            # became invisible to sync (2026-08-01 review).
            for root in sorted(inventory):
                if root in covered_roots:
                    continue
                for rel in inventory[root]:
                    if os.path.lexists(os.path.join(home_dir, rel)):
                        drift.append(
                            f"~/{rel}: deployed under a target the manifest no "
                            "longer carries (run scripts/sync.sh --apply)")
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

    # Informational only for what the reader *finds*: hints and the missing-data
    # warning never block the throttle. A reader that cannot run is the other
    # case and does block it, because "no hints today" and "the hints mechanism
    # is broken" are not the same report. (This comment described the behaviour
    # from before that distinction existed; corrected 2026-08-04.)
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
        if exp.returncode != 0:
            # "The reader crashed" and "there is nothing to report" are opposite
            # facts and used to produce identical silence: a non-zero exit
            # became `{}`, which then took the no-hints branch and said nothing.
            # A ledger row the reader cannot handle therefore retired the hints
            # *and* the routing revision behind them without a word
            # (2026-08-03 review). This is the loudest thing an informational
            # check may do: report it and withhold the stamp, the same as any
            # other subprocess failure here.
            checks_completed = False
            detail = (exp.stderr or exp.stdout).strip().splitlines()[-3:]
            findings.append(
                f"dispatch-experience reader failed (exit {exp.returncode}); "
                "hints and routing revision are both unavailable until it is "
                "fixed:\n" + "\n".join(detail)
            )
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
        # The reader now survives a damaged row instead of dying on it, which
        # traded a loud failure for a quiet one: the numbers just get smaller.
        # Informational, not throttle-blocking - the check ran fine, the file
        # is what has a problem - but it has to be said somewhere, and this is
        # the only place that reads the report without being asked.
        if report.get("unusable_rows"):
            findings.append(
                f"experience ledger damage: {report['unusable_rows']} row(s) "
                "unreadable or wrongly typed; they count toward no cohort above"
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
        from datetime import datetime, timedelta, timezone
        # experience-log's ROLES: the set `--from-pending` will accept. Keying
        # the *report* on it was the defect, not the set itself. Enumerating
        # loggable roles here and skipping everything else meant an agent type
        # the machine really dispatches but this harness does not route -
        # `claude-code-guide` and the built-in `Explore` are the ones observed -
        # was unloggable and unreported at the same time, which is the exact
        # silence the 2026-08-06 pass set out to end and only half ended: it
        # added the three diagnostic roles and left the rest outside
        # (2026-08-06 review, reproduced against a real 11-day-old stub).
        #
        # A staged completion with a dispatch id the ledger never answered is
        # un-reconciled whatever its role. The role now picks the *remedy*, not
        # whether the operator is told: a role the logger accepts gets
        # `experience-log`, one it does not gets `experience-stage --abandon`,
        # which matches on dispatch id alone and therefore always works.
        loggable_roles = {
            "explore", "mech-executor", "executor", "plan-verifier",
            "verifier", "security-reviewer", "security-executor",
            "general-purpose", "claude", "codex:codex-rescue",
        }
        ledger_path = os.environ.get(
            "AGENT_EXPERIENCE_LEDGER",
            os.path.expanduser("~/.agents/telemetry/experience.jsonl"),
        )
        reconciled = set()
        untied: list[str] = []
        # The one thing `verifier-quota` is documented as unable to count. It
        # keys on `subagent_type`, and a Codex verifier reached through the
        # bridge arrives under the bridge's name, which covers every Codex role
        # - so listing it would refuse a second *implementation* dispatch. The
        # gap is disclosed there rather than half-enforced; this is the other
        # half, after the fact, where the role is known because QC wrote it.
        # Detection, not prevention: the ledger has the field the payload lacks.
        unseen_verifiers: list[str] = []
        native_verifier_sessions: set[str] = set()
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        try:
            # errors="replace": decoding precedes json.loads, so a half-written
            # multi-byte character would otherwise abort the whole check rather
            # than cost one row (2026-07-30 re-review).
            with open(ledger_path, encoding="utf-8", errors="replace") as stream:
                for raw in stream:
                    if not raw.strip():
                        continue
                    try:
                        logged = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    # Valid JSON is not necessarily an object. `[]`, `"junk"`,
                    # `42` and `null` all parse and all raise on `.get()` -
                    # an AttributeError, which the `except OSError` below does
                    # not catch either, so one such row aborted the entire
                    # check (2026-07-31 re-review, second pass).
                    if not isinstance(logged, dict):
                        continue
                    if logged.get("role") == "verifier":
                        try:
                            seen = datetime.fromisoformat(logged.get("ts", ""))
                        except (TypeError, ValueError):
                            seen = None
                        if seen is not None and seen > week_ago:
                            source = logged.get("request_source")
                            session = str(logged.get("session") or "")
                            if source == "claude-code-plugin-codex":
                                unseen_verifiers.append(session or "(no session)")
                            elif source == "claude-code" and session:
                                native_verifier_sessions.add(session)
                    if logged.get("dispatch_id"):
                        reconciled.add(logged["dispatch_id"])
                        # The other half of the same question. A stub the
                        # ledger never answered is one failure; a ledger record
                        # that ties to no stub is the other, and until
                        # 2026-08-13 nothing looked for it. Two replay runs
                        # that day filed outcomes under ids of their own -
                        # one dropping the session prefix, one inventing
                        # `rv-policy-01` - and both printed a clean success.
                        #
                        # A staged id is always `<session>:<agent>`, from the
                        # hook and from `experience-stage` alike, so the shape
                        # is the test. `experience-log` now says so at write
                        # time; this is the weekly view for the case where
                        # nobody read it.
                        if not UNTIED_ID.match(logged["dispatch_id"]):
                            try:
                                when = datetime.fromisoformat(
                                    logged.get("ts", ""))
                            except (TypeError, ValueError):
                                when = None
                            if when is not None and when > week_ago:
                                untied.append(logged["dispatch_id"])
        except OSError:
            pass
        pending_path = os.environ.get(
            "AGENT_EXPERIENCE_PENDING",
            os.path.expanduser("~/.agents/telemetry/experience-pending.jsonl"),
        )
        cutoff = datetime.now(timezone.utc).timestamp() - 86400
        stale = {}
        unroutable = set()
        # Same `errors="replace"` as the ledger read above, and for the same
        # reason twice over: the pending file is the one a hook appends to on
        # every subagent stop, and a UnicodeDecodeError is a ValueError, not an
        # OSError - so it escaped the handler below, aborted the whole check,
        # and discarded every finding collected before this point
        # (2026-07-31 re-review).
        with open(pending_path, encoding="utf-8", errors="replace") as stream:
            for raw in stream:
                if not raw.strip():
                    continue
                try:
                    row = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if not isinstance(row, dict):  # see the ledger read above
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
                loggable = (agent_type in loggable_roles
                            or "codex" in agent_type)
                # A stub with no dispatch id predates the field and cannot be
                # reconciled by any command this finding recommends, all of
                # which require `--dispatch-id`. The pending hook now always
                # writes one, so no new stub can land here.
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
                    if not loggable:
                        unroutable.add(dispatch_id)
        if stale:
            unroutable = sorted(unroutable & set(stale))
            findings.append(
                "un-reconciled dispatches (launched or completed but never "
                "logged to the experience ledger; log with experience-log "
                "--from-pending --dispatch-id <id> --outcome <o>, or retire a "
                "native Codex launch that never ran with experience-stage "
                "--cancel):\n" + "\n".join(sorted(stale))
            )
            if unroutable:
                # experience-log refuses a role it does not route, so naming
                # these without naming the command that does work would leave
                # the operator with a finding and no way to clear it.
                findings.append(
                    "of those, this harness routes no role for "
                    + ", ".join(unroutable)
                    + "; experience-log will refuse them. Close each with "
                    "experience-stage --abandon --dispatch-id <id> --reason "
                    "<why>, which matches on the id alone"
                )
        if untied:
            # Aggregated, and only three names. Sixty-one of these are one
            # operator's own labels from a single day in August, already
            # diagnosed and written up; reporting each of them weekly would
            # teach the reader to skip the section that also carries the new
            # one. The count is the signal, the examples are the handle.
            findings.append(
                f"{len(untied)} ledger record(s) in the last 7 days carry a "
                "dispatch id that cannot tie to a staged stub (a staged id is "
                "`<session>:<agent>`), so they reconcile nothing: "
                + ", ".join(sorted(set(untied))[:3])
                + ("..." if len(set(untied)) > 3 else "")
                + ". Expected for a dispatch that was never staged (another "
                "provider, hooks off); a typo or an invented id otherwise"
            )
        if unseen_verifiers:
            # Counted, not judged. The quota is per prompt and the ledger has no
            # prompt id, so a bridge verifier beside a native one in the same
            # session is a question rather than a violation - a long session
            # legitimately spends one per task. What is certain is that the gate
            # never saw these, which is exactly what it says about itself.
            both = sorted(set(unseen_verifiers) & native_verifier_sessions)
            findings.append(
                f"{len(unseen_verifiers)} outcome verifier(s) in the last 7 days "
                "ran through the Codex bridge, where the one-verifier quota "
                "cannot see them (main/claude/hooks/verifier-quota.py documents "
                "why it cannot). "
                + (f"{len(both)} of them shared a session with a native "
                   "verifier, so check whether one prompt spent two: "
                   + ", ".join(s[:8] for s in both[:3])
                   if both else
                   "None shared a session with a native verifier, so nothing "
                   "here suggests a double spend")
            )
    except (OSError, ValueError):
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

    # leaf-redispatch cannot be audited the same way: its carrier is absent on
    # every healthy dispatch and present only on the violation it exists to
    # refuse, so "never fired" and "can no longer fire" produce identical
    # evidence. The runtime version is the only thing that moves, and the field
    # is undocumented payload shape that a release may change without saying so.
    try:
        validated = carrier_validated_on()
        live = live_runtime_version()
        if validated and live and live > validated:
            findings.append(
                "leaf-redispatch carrier unvalidated on this runtime: the gate "
                f"reads `agent_type`, last observed on Claude Code "
                f"{'.'.join(map(str, validated))}, and this machine runs "
                f"{'.'.join(map(str, live))}. Nothing here can tell a fleet that "
                "never re-dispatches from a gate that stopped seeing its field. "
                "Re-validate with one dispatch whose leaf attempts a nested "
                "dispatch (expect exit 2), then advance CARRIER_VALIDATED_ON in "
                "main/claude/hooks/leaf-redispatch.py"
            )
    except (OSError, ValueError):
        pass

    if checks_completed:
        try:
            os.makedirs(os.path.dirname(STAMP), exist_ok=True)
            with open(STAMP, "w", encoding="utf-8") as stamp:
                stamp.write(str(int(time.time())))
        except OSError as exc:
            findings.append(f"integrity throttle update failed: {exc}")
except DeadlineExhausted as exc:
    # Not a check failure: the checks that ran are still valid, and the ones
    # that did not are simply unknown. Withholding the stamp is what makes the
    # next session pick them up, so say that rather than let a partial run look
    # complete.
    checks_completed = False
    # Every other finding here names a command; this one used to name only the
    # symptom, so a run that kept stopping had no stated way out and would have
    # become the standing alarm this file warns about three times over.
    findings.append(
        f"{exc}; the remaining checks did not run and are retried next session. "
        "Clear the drift they were slow on (scripts/sync.sh --apply), or if the "
        f"run is legitimately longer than {BUDGET:.0f}s, raise BUDGET and the "
        "SessionStart timeout in settings.json together"
    )
except Exception as exc:
    checks_completed = False
    findings.append(f"check failed unexpectedly: {exc}")

if findings:
    print("[weekly-integrity] issues found — relay these to the user:")
    for f in findings:
        print(f)
sys.exit(0)
