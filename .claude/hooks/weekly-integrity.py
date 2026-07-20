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
    try:
        r = subprocess.run(
            ["git", "-C", claude_dir, "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if r.returncode != 0:
            checks_completed = False
            detail = (r.stderr or r.stdout).rstrip()
            findings.append(f"contract-repo check failed (exit {r.returncode}):\n{detail}")
        elif r.stdout.strip():
            findings.append(
                "contract-repo drift (uncommitted changes in ~/.claude):\n"
                + r.stdout.rstrip()
            )
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
