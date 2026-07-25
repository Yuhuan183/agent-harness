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
`\( -o \)`, `-not`, and `-exec`. The failure surfaces as an `rtk:` message rather
than the tool's own error. Rerun with an absolute path (`/usr/bin/find`,
`/usr/bin/grep`) to bypass the rewrite.

Bare `find` and `grep` are not `rtk`: Claude Code shadows them with its embedded
`bfs` and `ugrep`, which take the usual flags. Reach for the absolute path only
after an `rtk:` message actually appears.
