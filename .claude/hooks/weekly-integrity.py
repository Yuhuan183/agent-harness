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
        elif os.path.isdir(os.path.join(harness_repo, ".claude")):
            synced = [
                "CLAUDE.md", "README.md", "RTK.md", "settings.json",
                "agents", "hooks", "prompts", "scripts", "sh", "tests",
                "examples", "plans/orchestration-plan.md",
                "skills/baton-dispatch", "skills/provider-routing",
                "skills/headroom-protocol", "skills/speak-human-tw",
                "skills/experience-ledger",
            ]
            drift = []
            for p in synced:
                src = os.path.join(harness_repo, ".claude", p)
                if not os.path.exists(src):
                    continue
                r = subprocess.run(
                    ["rsync", "-a", "--links", "-n", "--itemize-changes",
                     src, os.path.dirname(os.path.join(claude_dir, p)) + "/"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if r.returncode != 0:
                    checks_completed = False
                    detail = (r.stderr or r.stdout).rstrip()
                    findings.append(
                        f"contract-repo check failed (rsync exit {r.returncode}, {p}):\n{detail}"
                    )
                    break
                for line in r.stdout.splitlines():
                    # rsync -n itemized lines starting with '.' are unchanged;
                    # anything else means content would be copied (drift).
                    if line and not line.startswith(".") and not line.endswith("/"):
                        drift.append(f"{p}: {line}")
            if drift:
                findings.append(
                    "contract-repo drift (~/.claude differs from repo copy — "
                    "run scripts/sync.sh --apply or commit repo changes):\n"
                    + "\n".join(drift)
                )
        # else: no git repo and no harness checkout — nothing to compare
        # against; skip the drift check without blocking the throttle.
    except (OSError, subprocess.TimeoutExpired) as exc:
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

    # Informational only: surface dispatch-experience hints when any exist.
    # Best-effort — a failure here neither blocks the throttle nor alarms.
    try:
        exp = subprocess.run(
            [os.path.expanduser(
                "~/.agents/skills/experience-ledger/scripts/experience-report"),
             "--days", "30"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        hints = [l for l in exp.stdout.splitlines() if l.startswith("hint:")]
        if exp.returncode == 0 and hints:
            findings.append("dispatch-experience hints (30d):\n" + "\n".join(hints))
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
