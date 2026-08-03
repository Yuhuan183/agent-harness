# RTK Guide

`rtk` filters common CLI output before it enters model context. The `settings.json` PreToolUse hook rewrites supported commands automatically and fails open when RTK is absent.

## Verify

```bash
rtk --version
rtk gain
which rtk
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

## When a rewritten command fails

`rtk` subcommands accept a narrower flag set than the tools they stand in for —
`rtk find`, for example, rejects compound predicates and actions such as
`\( -o \)`, `-not`, and `-exec`. Rerun with an absolute path (`/usr/bin/find`,
`/usr/bin/grep`) to bypass the rewrite.

A rejected flag has two failure signatures, not one, and the second is the
dangerous one:

- an `rtk:` message, which is unmistakable; or
- **the substituted tool's own usage error**, because the rewrite can hand the
  command to a different program than the one written. `rg -n <pat> <paths>
  --glob '*.md'` becomes a `grep` invocation, `grep` rejects `--glob`, and the
  wrapper still prints `0 matches for '<pat>'` — a definitive-looking negative
  for a search that never ran. Exit status is non-zero, but the text is what a
  model reads (verified against rtk 0.42.4, 2026-08-02).

So the rule is about the result, not the prefix: **never record a "no hits"
conclusion from a rewritten command.** If a negative result is load-bearing,
re-run it with an absolute path and compare. A non-empty result needs no such
confirmation — only the empty one is ambiguous.

Bare `find` and `grep` are not `rtk`: Claude Code shadows them with its embedded
`bfs` and `ugrep`, which take the usual flags. Reach for the absolute path only
after an `rtk:` message actually appears.
