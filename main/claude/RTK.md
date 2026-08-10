# RTK Guide

`rtk` filters common CLI output before it enters model context. The `settings.json` PreToolUse hook rewrites supported commands automatically and fails open when RTK is absent.

## Who owns the hook

The hook is registered by this repo's `settings.json` as `rtk hook claude` — not by
rtk's own installer. Keep it that way:

- **Never run `rtk init` or `rtk init -g`.** Per its own `--help` it installs a
  hook and writes an instruction block into the global assistant directory —
  both repo-owned here (`~/.claude/settings.json`, `~/.claude/CLAUDE.md`), so it
  would fight the deployment rather than add to it. Headroom used to install rtk
  this way, and its cleanup still deletes `~/.claude/hooks/rtk-rewrite.sh` and
  prunes hook entries matching `rtk-rewrite` / `rtk rewrite` on every
  `headroom wrap` run; whether today's `rtk init` still emits those exact names
  is unverified, so treat the collision as likely rather than certain.
- `rtk gain` ends with `[warn] No hook installed — run rtk init -g`. Expected here;
  it only means rtk did not install the hook itself. Do not act on it.
- Codex gets no hook: `rtk hook` supports claude, cursor, gemini, copilot, droid and
  vibe, but not codex. That asymmetry is why the Codex contract carries a prefix
  instruction and the Claude contract does not.

## Verify

```bash
rtk --version
which rtk
rtk gain                    # savings summary (the "no hook" warn is expected)
rtk hook check git status   # dry-run: how the hook would rewrite a command
```

If `rtk gain` is unavailable, check for the unrelated `reachingforthejack/rtk` name collision.

## Direct commands

```bash
rtk gain             # Savings summary
rtk gain --history   # Per-command history
rtk discover         # Missed filtering opportunities
rtk proxy <cmd>      # Raw command for debugging
```

Use normal commands such as `git status`; the hook handles supported rewrites.
`rtk hook check <cmd>` shows the rewrite without running it — `git status` →
`rtk git status`, `cat F` → `rtk read F`, `grep -rn P D` → `rtk grep -rn P D`.

## When a rewritten command fails

`rtk` subcommands accept a narrower flag set than the tools they stand in for —
`rtk find`, for example, rejects compound predicates and actions such as
`\( -o \)`, `-not`, and `-exec`. Rerun with an absolute path (`/usr/bin/find`,
`/usr/bin/grep`) to bypass the rewrite.

A rejected flag can surface in two ways, and the second is the dangerous one:

- an `rtk:` message, which is unmistakable. `rtk find … -not` still fails this way
  (verified against rtk 0.45.0, 2026-08-10); or
- **the substituted tool's own usage error**, because the rewrite can hand the
  command to a different program than the one written. On rtk 0.42.4 (2026-08-02)
  `rg -n <pat> <paths> --glob '*.md'` became a `grep` invocation, `grep` rejected
  `--glob`, and the wrapper still printed `0 matches for '<pat>'` — a
  definitive-looking negative for a search that never ran.

That second signature **no longer reproduces on 0.45.0**: `rtk rg` runs ripgrep
natively, passes `--glob` through, and a genuine no-match returns empty output
rather than a fabricated count. Treat it as fixed upstream, not as impossible —
the contract keeps the rule because the version varies per machine and the failure
is silent when it does happen.

So the rule is about the result, not the prefix: **never record a "no hits"
conclusion from a rewritten command.** If a negative result is load-bearing,
re-run it with an absolute path and compare. A non-empty result needs no such
confirmation — only the empty one is ambiguous.

Bare `find` and `grep` are not `rtk`: Claude Code shadows them with its embedded
`bfs` and `ugrep`, which take the usual flags. Reach for the absolute path only
after an `rtk:` message actually appears.
