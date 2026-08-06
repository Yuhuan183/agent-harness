#!/usr/bin/env python3
"""Run one leaf-role contract at a named model/effort rung, in isolation.

Why this exists. Sampling a second rung used to mean editing a deployed agent
frontmatter or a profile preset, which changes the route for every session on
the machine and leaves a restore step nobody can be trusted to remember. It
also ran the sample through whatever proxy the operator's shell had configured,
so the surface under test could be rewritten before the agent read it — s10's
2026-08-06 rows caught two runs disclosing exactly that.

This runner takes neither risk. It starts its own `claude --print` process with
the rung on the command line, so nothing under `~/.claude` is touched and there
is nothing to restore, and it detaches the sample from the operator's proxy so
the fixture reaches the agent as written.

Detaching takes two steps, and the second one is not obvious. Clearing
`ANTHROPIC_BASE_URL` from the child environment is not enough: a project's
`.claude/settings.local.json` can carry an `env` block that puts it back, and
this repository's does. So the run also happens in a scratch directory outside
any project, with the fixture reachable through `--add-dir`. Measured
2026-08-06: with `cwd` inside the repo the sample showed up in the proxy log as
its own session; from outside, it does not.

What it is not: the role runs here as a session, not as a subagent. The
Agent-tool dispatch path is not exercised, so no SubagentStart/Stop hook fires
and no pending stub is staged - a record for one of these runs has to name
`--role/--model/--effort` by hand, and `route_source` will be `explicit`. Use
it to compare rungs, not to accumulate cohort samples.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AGENTS = REPO / "main/claude/agents"

# Cleared, not overridden: an empty ANTHROPIC_BASE_URL is not the same as an
# absent one, and a proxy that rewrites the fixture invalidates the sample
# rather than degrading it.
PROXY_VARS = ("ANTHROPIC_BASE_URL", "ANTHROPIC_CUSTOM_HEADERS", "ANTHROPIC_MODEL")


def parse_agent(role: str) -> tuple[dict, str]:
    """Return (frontmatter, body) for a repo agent contract."""
    path = AGENTS / f"{role}.md"
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", text, re.S)
    if not match:
        raise SystemExit(f"{path}: no frontmatter")
    fields = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields, match.group(2).strip()


def build_argv(args, frontmatter: dict, body: str) -> list[str]:
    argv = [
        "claude", "--print", args.prompt,
        "--model", args.model,
        "--effort", args.effort,
        "--append-system-prompt", body,
        # Deterministic surface: cwd, env, git status and memory paths differ
        # between operators and would show up as unexplained cross-run variance.
        "--exclude-dynamic-system-prompt-sections",
        # The role's own settings must not leak in from the machine. An inline
        # JSON object is the documented way to say "these and nothing else".
        "--settings", json.dumps({"hooks": {}}),
        "--strict-mcp-config",
        "--permission-mode", "manual",
    ]
    tools = frontmatter.get("tools")
    if tools:
        argv += ["--allowedTools", *[t.strip() for t in tools.split(",") if t.strip()]]
    disallowed = frontmatter.get("disallowedTools")
    if disallowed:
        argv += ["--disallowedTools",
                 *[t.strip() for t in disallowed.split(",") if t.strip()]]
    for extra in args.add_dir:
        argv += ["--add-dir", extra]
    return argv


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True, help="agent contract under main/claude/agents")
    parser.add_argument("--model", required=True, help="concrete id or alias, e.g. claude-opus-5")
    parser.add_argument("--effort", required=True,
                        choices=["low", "medium", "high", "xhigh", "max"])
    parser.add_argument("--prompt", help="brief text; use --prompt-file to read it")
    parser.add_argument("--prompt-file", type=Path)
    parser.add_argument("--add-dir", action="append", default=[],
                        help="directory the run may read (repeatable)")
    parser.add_argument("--out", type=Path, help="write the final report here")
    parser.add_argument("--seed-label", default="", help="label echoed in the summary line")
    parser.add_argument("--cwd", help="run directory; defaults to a fresh temp dir "
                        "outside every project, which is what keeps project settings "
                        "and CLAUDE.md out of the sample")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--dry-run", action="store_true",
                        help="print the argv that would run and exit 0")
    args = parser.parse_args()

    if not args.prompt and not args.prompt_file:
        parser.error("one of --prompt or --prompt-file is required")
    if args.prompt_file:
        args.prompt = args.prompt_file.read_text(encoding="utf-8")

    frontmatter, body = parse_agent(args.role)
    argv = build_argv(args, frontmatter, body)

    if args.dry_run:
        print(json.dumps(argv, ensure_ascii=False))
        return 0

    env = {k: v for k, v in os.environ.items() if k not in PROXY_VARS}
    # Never the repository: its project settings would re-inject the proxy and
    # its CLAUDE.md would join the surface under test.
    neutral_cwd = args.cwd or tempfile.mkdtemp(prefix="rung-run-")
    try:
        result = subprocess.run(argv, capture_output=True, text=True,
                                timeout=args.timeout, env=env, cwd=neutral_cwd)
    except subprocess.TimeoutExpired:
        print(f"{args.seed_label or args.role}: TIMEOUT after {args.timeout}s",
              file=sys.stderr)
        return 124
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        return result.returncode

    report = result.stdout
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
    else:
        sys.stdout.write(report)
    label = args.seed_label or args.role
    print(f"{label}: {args.model}/{args.effort} ok, {len(report.split())} words",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
