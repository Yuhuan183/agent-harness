#!/usr/bin/env bash
# Installs the agent-harness agent-launch shell functions into a zsh startup file.
# Idempotent: the marked block is stripped and re-appended, so re-running never
# duplicates. Machine-local only; NOT part of scripts/sync.sh or the deployment
# manifest. This heredoc is the canonical function definition; docs/setup.md
# describes the public command matrix without duplicating the implementation.
# Usage:
#   scripts/install-zsh-functions.sh            # dry-run: show block and diff
#   scripts/install-zsh-functions.sh --apply    # write it (backs up first)
#   scripts/install-zsh-functions.sh --print-block
#   ZSHRC=~/.config/zsh/.zshrc scripts/install-zsh-functions.sh --apply

# Re-exec under real bash. This script uses process substitution (the diff at
# the dry-run step), which is disabled when the file is invoked via `sh` -- on
# macOS that is bash in POSIX mode, which fails to parse `<(...)`. Re-exec runs
# before the parser reaches that line, so `sh install-zsh-functions.sh` works.
if [ -z "${BASH_VERSION:-}" ] || [ -n "${POSIXLY_CORRECT:-}" ]; then
  exec bash "$0" "$@"
fi
set -euo pipefail

ZSHRC="${ZSHRC:-$HOME/.zshrc}"
BEGIN='# >>> agent-harness auto-mode functions >>>'
END='# <<< agent-harness auto-mode functions <<<'
APPLY=0
PRINT_BLOCK=0
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --print-block) PRINT_BLOCK=1 ;;
    -h|--help) sed -n '2,11p' "$0"; exit 0 ;;
    *) printf 'ERROR: unknown argument: %s\n' "$arg" >&2; exit 2 ;;
  esac
done

read -r -d '' BLOCK <<'EOF' || true
# >>> agent-harness auto-mode functions >>>
# Source: agent-harness/scripts/install-zsh-functions.sh.
# Auto Mode keeps each agent's normal safety boundary; never alias an agent to
# its fully-bypassing --dangerously-* flag.
_agent_harness_headroom_wrap() {
  local agent="$1"
  shift
  if ! command headroom wrap "$agent" --help >/dev/null 2>&1; then
    printf "h%s: installed Headroom does not support 'wrap %s'; refusing to launch the agent directly.\n" \
      "$agent" "$agent" >&2
    return 127
  fi
  command headroom wrap "$agent" "$@"
}

claude-auto() {
  command claude --permission-mode auto "$@"
}

codex-auto() {
  command codex -a on-request -s workspace-write "$@"
}

agy-auto() {
  command agy --mode accept-edits "$@"
}

hclaude() {
  _agent_harness_headroom_wrap claude -- "$@"
}

hcodex() {
  _agent_harness_headroom_wrap codex -- "$@"
}

hagy() {
  _agent_harness_headroom_wrap agy -- "$@"
}

hclaude-auto() {
  hclaude --permission-mode auto "$@"
}

hcodex-auto() {
  hcodex -a on-request -s workspace-write "$@"
}

hagy-auto() {
  hagy --mode accept-edits "$@"
}
# <<< agent-harness auto-mode functions <<<
EOF

# Before this installer existed, docs/setup.md instructed users to paste this
# exact unmarked block. Remove only that historical byte-for-byte form during
# migration; a locally edited lookalike is user-owned and must survive.
read -r -d '' LEGACY_BLOCK <<'EOF' || true
# Agent CLI session modes
claude-auto() {
  command claude --permission-mode auto "$@"
}

codex-auto() {
  command codex -a never -s workspace-write "$@"
}

hclaude-auto() {
  command headroom wrap claude --no-context-tool -- \
    --permission-mode auto "$@"
}

hcodex-auto() {
  command headroom wrap codex --no-context-tool -- \
    -a never -s workspace-write "$@"
}
EOF

if [[ $PRINT_BLOCK -eq 1 ]]; then
  printf '%s\n' "$BLOCK"
  exit 0
fi

current=""
[[ -f "$ZSHRC" ]] && current="$(cat "$ZSHRC")"

# Drop any existing marked block (BEGIN..END inclusive), migrate the exact
# historical unmarked block, then trim trailing blanks.
stripped="$(printf '%s\n' "$current" | awk -v b="$BEGIN" -v e="$END" '
  $0==b {skip=1; next}
  $0==e {skip=0; next}
  !skip {print}
')"
# Bash parameter replacement treats the needle as a glob pattern. Escape the
# legacy block's literal backslashes before matching its line continuations.
legacy_pattern="${LEGACY_BLOCK//\\/\\\\}"
stripped="${stripped//$legacy_pattern/}"
stripped="$(printf '%s\n' "$stripped" \
  | awk 'NF{n=NR} {a[NR]=$0} END{for(i=1;i<=n;i++)print a[i]}')"

if [[ -n "$stripped" ]]; then
  desired="$stripped"$'\n\n'"$BLOCK"
else
  desired="$BLOCK"
fi

if [[ -f "$ZSHRC" && "$desired" == "$(cat "$ZSHRC")" ]]; then
  printf 'already up to date: %s\n' "$ZSHRC"
  exit 0
fi

if [[ $APPLY -ne 1 ]]; then
  printf '[dry-run] would write these functions to %s:\n\n%s\n\n' "$ZSHRC" "$BLOCK"
  printf '[dry-run] diff (current -> desired):\n'
  diff <(printf '%s\n' "$current") <(printf '%s\n' "$desired") || true
  printf '\ndry-run complete; re-run with --apply to write.\n'
  exit 0
fi

if [[ -f "$ZSHRC" ]]; then
  backup="$ZSHRC.agent-harness.$(date +%Y%m%d-%H%M%S).bak"
  cp "$ZSHRC" "$backup"
  printf 'backup: %s\n' "$backup"
fi
printf '%s\n' "$desired" > "$ZSHRC"
printf 'wrote: %s\n' "$ZSHRC"
printf 'run "source %s" or open a new terminal to activate.\n' "$ZSHRC"
