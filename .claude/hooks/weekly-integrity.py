#!/usr/bin/env python3
"""Weekly-throttled integrity check, run from SessionStart.

Deterministic checks only: contract-repo drift (git status) and nested-delegation
scan. Findings and check failures are printed to stdout for the active session.
The hook is fail-open, but its throttle advances only after both checks run.
"""
import os
import subprocess
import sys
import time

PERIOD = 7 * 86400
STAMP = os.path.expanduser("~/.claude/telemetry/.integrity-last-run")


def load_deployment_manifest(repo):
    """Return validated repo-relative source and HOME-relative target pairs."""
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
            if len(fields) != 2 or not all(fields):
                raise ValueError(f"malformed deployment manifest line {line_number}")
            source, target = fields
            prefixes = (".agents/", ".claude/", ".codex/")
            if not source.startswith(prefixes) or not target.startswith(prefixes):
                raise ValueError(f"unsafe deployment manifest line {line_number}")
            if any(part in ("", ".", "..") for part in source.split("/")) \
                    or any(part in ("", ".", "..") for part in target.split("/")):
                raise ValueError(f"unsafe deployment path line {line_number}")
            if source in sources or target in targets:
                raise ValueError(f"duplicate deployment manifest line {line_number}")
            sources.add(source)
            targets.add(target)
            pairs.append((source, target))
    if not pairs:
        raise ValueError("deployment manifest is empty")
    return pairs

try:
    if os.path.exists(STAMP) and time.time() - os.path.getmtime(STAMP) < PERIOD:
        sys.exit(0)

    findings = []
    checks_completed = True
    claude_dir = os.path.expanduser("~/.claude")
    # ~/.claude is normally populated by scripts/sync.sh rsync from the harness
    # repo, not a git checkout. Drift check adapts to the deployment model:
    # git status when ~/.claude is itself a repo, otherwise an rsync dry-run
    # against the repo's tracked .claude/ copy (same paths sync.sh manages).
    harness_repo = os.environ.get(
        "AGENT_HARNESS_REPO", os.path.expanduser("~/WorkSpace/agent-harness")
    )
    try:
        if os.path.isdir(os.path.join(claude_dir, ".git")):
            r = subprocess.run(
                ["git", "-C", claude_dir, "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=10,
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
        if not os.path.isdir(os.path.join(harness_repo, ".claude")):
            # A managed deployment without a reachable source checkout has no
            # drift monitoring at all — that is a finding, not a silent skip,
            # and the throttle must not advance past it.
            checks_completed = False
            findings.append(
                "deployment drift check unavailable: harness checkout not found at "
                f"{harness_repo}; set AGENT_HARNESS_REPO to the source checkout "
                "(drift monitoring is suspended until then)"
            )
        else:
            drift = []
            for source_rel, target_rel in load_deployment_manifest(harness_repo):
                src = os.path.join(harness_repo, source_rel)
                if not os.path.lexists(src):
                    raise ValueError(f"deployment source missing: {source_rel}")
                deployed = os.path.join(os.path.expanduser("~"), target_rel)
                if os.path.isdir(src):
                    r = subprocess.run(
                        ["rsync", "-a", "--links", "--delete", "--delete-excluded",
                         "--exclude", "__pycache__/", "--exclude", "*.pyc",
                         "--exclude", ".DS_Store", "-n", "--itemize-changes",
                         src, os.path.dirname(deployed) + "/"],
                        capture_output=True, text=True, timeout=10,
                    )
                else:
                    same = subprocess.run(
                        ["cmp", "-s", src, deployed], timeout=10,
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
                        f"{target_rel}):\n{detail}"
                    )
                    break
                for line in r.stdout.splitlines():
                    # rsync -n itemized lines starting with '.' are unchanged;
                    # anything else means content would be copied (drift).
                    if line and not line.startswith(".") and not line.endswith("/"):
                        drift.append(f"~/{target_rel}: {line}")
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
            timeout=10,
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

    # Pin-drift check is skipped when the deployment lacks the resolver
    # (e.g. a partially synced ~/.claude); nothing to compare against.
    routing_script = os.path.join(claude_dir, "scripts", "model-routing")
    try:
        if not os.access(routing_script, os.X_OK):
            pins = None
        else:
            pins = subprocess.run(
                [routing_script, "check-pins"],
                capture_output=True,
                text=True,
                timeout=10,
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

    codex_routing = os.path.expanduser("~/.codex/scripts/model-routing")
    try:
        if os.access(codex_routing, os.X_OK):
            validated = subprocess.run(
                [codex_routing, "validate"], capture_output=True, text=True, timeout=10
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

    # Informational only: surface dispatch-experience hints or a missing-data
    # warning. Best-effort — a failure here neither blocks the throttle nor alarms.
    try:
        exp = subprocess.run(
            [os.path.expanduser(
                "~/.agents/skills/experience-ledger/scripts/experience-report"),
             ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        hints = [l for l in exp.stdout.splitlines() if l.startswith("hint:")]
        if exp.returncode == 0 and hints:
            findings.append("dispatch-experience hints:\n" + "\n".join(hints))
        elif exp.returncode == 0 and "no records" in exp.stdout:
            findings.append(
                "dispatch-experience gap: no reviewed outcomes in the configured window; "
                "log the next comparable dispatch after quality-check"
            )
    except (OSError, subprocess.TimeoutExpired):
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
