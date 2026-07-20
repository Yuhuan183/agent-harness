#!/usr/bin/env python3
"""Warn when Claude Code cannot enforce the reviewer tool boundary.

SessionStart hook; silent on supported builds and fail-open on every path.
An optional version string argument exists only for deterministic pipe tests.
"""
import re
import subprocess
import sys


MINIMUM = (2, 1, 207)
RESTRICTED_ROLES = "plan-verifier/security-reviewer[-xhigh]"


def parse_version(raw):
    match = re.search(r"\b(\d+)\.(\d+)\.(\d+)\b", raw)
    return tuple(map(int, match.groups())) if match else None


def main(argv):
    raw = ""
    try:
        if len(argv) > 1:
            raw = " ".join(argv[1:])
        else:
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

    version = parse_version(raw)
    if version is None:
        print(
            "[runtime-guard] Claude Code version unknown; do not dispatch "
            f"{RESTRICTED_ROLES} because their read-only tool boundary is unverified."
        )
    elif version < MINIMUM:
        current = ".".join(map(str, version))
        required = ".".join(map(str, MINIMUM))
        print(
            f"[runtime-guard] Claude Code {current} < {required}; do not dispatch "
            f"{RESTRICTED_ROLES}. Upgrade and restart before using those roles."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
