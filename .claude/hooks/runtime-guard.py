#!/usr/bin/env python3
"""Reviewer tool-boundary guard for Claude Code.

Two modes share one cached version probe:
- SessionStart (default): warn when the runtime cannot enforce the read-only
  reviewer boundary; always exit 0.
- PreToolUse --gate: block (exit 2) dispatch of capability-sensitive read-only
  reviewers when the version is below MINIMUM or unknown.

Unexpected internal errors stay fail-open; the deliberate gate block is the
documented exception. An optional version string argument exists only for
deterministic pipe tests (it also bypasses the cache).
"""
import json
import os
import re
import shutil
import subprocess
import sys


MINIMUM = (2, 1, 207)
RESTRICTED_ROLES = ("plan-verifier", "security-reviewer")
CACHE = os.path.expanduser("~/.claude/telemetry/.runtime-version-cache")


def parse_version(raw):
    match = re.search(r"\b(\d+)\.(\d+)\.(\d+)\b", raw)
    return tuple(map(int, match.groups())) if match else None


def probe_version():
    """Return the raw version string, re-probing only when the binary changed."""
    binary = shutil.which("claude")
    mtime = int(os.stat(binary).st_mtime) if binary else 0
    try:
        with open(CACHE, encoding="utf-8") as fh:
            cached = json.load(fh)
        if (cached.get("binary") == binary and cached.get("mtime") == mtime
                and parse_version(cached.get("raw", ""))):
            return cached["raw"]
    except Exception:
        pass
    raw = ""
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        raw = f"{result.stdout} {result.stderr}"
    except Exception:
        raw = ""
    if parse_version(raw):
        try:
            os.makedirs(os.path.dirname(CACHE), exist_ok=True)
            with open(CACHE, "w", encoding="utf-8") as fh:
                json.dump({"binary": binary, "mtime": mtime, "raw": raw}, fh)
        except Exception:
            pass
    return raw


def gate(version):
    """PreToolUse gate: exit 2 blocks the Agent call for restricted roles."""
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    if payload.get("tool_name") != "Agent":
        return 0
    subagent = str((payload.get("tool_input") or {}).get("subagent_type", ""))
    if subagent not in RESTRICTED_ROLES:
        return 0
    if version is not None and version >= MINIMUM:
        return 0
    current = ".".join(map(str, version)) if version else "version unknown"
    required = ".".join(map(str, MINIMUM))
    print(
        f"[runtime-guard] blocked {subagent} dispatch: Claude Code {current} "
        f"cannot verify the read-only reviewer tool boundary (need >= {required}). "
        "Upgrade and restart, or run the review in the main session.",
        file=sys.stderr,
    )
    return 2


def main(argv):
    args = [arg for arg in argv[1:] if arg != "--gate"]
    gating = "--gate" in argv[1:]
    raw = " ".join(args) if args else probe_version()
    version = parse_version(raw)

    if gating:
        return gate(version)

    roles = "/".join(RESTRICTED_ROLES)
    if version is None:
        print(
            "[runtime-guard] Claude Code version unknown; dispatch of "
            f"{roles} will be blocked because their read-only tool boundary is unverified."
        )
    elif version < MINIMUM:
        current = ".".join(map(str, version))
        required = ".".join(map(str, MINIMUM))
        print(
            f"[runtime-guard] Claude Code {current} < {required}; dispatch of "
            f"{roles} will be blocked. Upgrade and restart before using those roles."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
