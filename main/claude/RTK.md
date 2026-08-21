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
- **Install rtk from a source Headroom does not manage.** That same cleanup pass
  deletes `~/.headroom/bin/rtk` outright, and `~/.local/bin/rtk` whenever it is a
  symlink into that directory — so an rtk left over from an older Headroom is
  removed by the next wrapped session. The hook's `command -v rtk` guard then
  makes it a silent no-op: filtering stops and nothing reports it. `which -a rtk`
  must not resolve into either path. This repo's own `rtk hook claude` command
  matches none of the cleanup's markers and is not at risk (re-checked against
  Headroom 0.36.0 source, 2026-08-20: the pruned hook-command markers are <!-- pinned 2026-08-21 -->
  `rtk-rewrite`, `rtk rewrite`, `lean-ctx-rewrite`, `lean-ctx-redirect` and
  `lean-ctx hook`, none of which is a substring of `rtk hook claude`). Pinned,
  because it names what one release's source contains rather than what any
  machine runs — this is a shared repo and the two are not the same claim.
  An earlier 0.35.0 stamp here was retracted on 2026-08-20 for being
  irreproducible locally; on 2026-08-21 that turned out to be two deployments
  read as one, so the retraction was wrong about the version and right about the
  remedy. The marker list above is what was read in 0.36.0 and nothing more.
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

- an `rtk:` message, which is unmistakable. `rtk find … -not` fails this way; or
- **the substituted tool's own usage error**, because the rewrite can hand the
  command to a different program than the one written. `rg -n <pat> <paths>
  --glob '*.md'` is rewritten to `rtk grep`, BSD `grep` rejects `--glob`, and the
  wrapper still prints `0 matches for '<pat>'` and exits 0 — a definitive-looking
  negative for a search that never ran.

Both signatures were run against a two-file fixture on 2026-08-10, before and
after upgrading, and the difference is real:

| rtk | `rg -n <pat> DIR --glob '*.md'` rewrites to | result |
|---|---|---|
| 0.42.4 | `rtk grep` → BSD `grep` | `unrecognized option --glob`, then `0 matches`, **exit 0**, while two files matched |
| 0.45.0 | `rtk rg` → real ripgrep | `--glob` honoured, one correct match, and a genuine no-match returns empty output with **exit 1** |

So the fabricated count is fixed — but it is fixed *per machine*, on a version
that has to actually be installed. An earlier 0.45.0 claim here came from
`brew info rtk`, which reports the formula's version next to `Not installed`.
Check `rtk --version`, never the package index.

`rtk rg` on 0.45.0 **shells out to real ripgrep**. Without it the rewrite fails
with `rtk: search failed: … (os error 2)` and exit 1 — loud, so no conclusion is
at risk, but every `rg` command dies. Install ripgrep alongside rtk.

So the rule is about the result, not the prefix: **never record a "no hits"
conclusion from a rewritten command.** If a negative result is load-bearing,
re-run it with an absolute path and compare. A non-empty result needs no such
confirmation — only the empty one is ambiguous.

Bare `find` and `grep` are not `rtk`: Claude Code shadows them with its embedded
`bfs` and `ugrep`, which take the usual flags. Reach for the absolute path only
after an `rtk:` message actually appears.
