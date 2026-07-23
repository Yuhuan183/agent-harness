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
