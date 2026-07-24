#!/usr/bin/env bash
# Installs the agent-harness Auto Mode shell functions into a zsh startup file.
# Idempotent: the marked block is stripped and re-appended, so re-running never
# duplicates. Machine-local only; NOT part of scripts/sync.sh or the deployment
# manifest. Canonical function definitions also live in docs/setup.md.
# Usage:
#   scripts/install-zsh-functions.sh            # dry-run: show block and diff
#   scripts/install-zsh-functions.sh --apply    # write it (backs up first)
#   ZSHRC=~/.config/zsh/.zshrc scripts/install-zsh-functions.sh --apply
set -euo pipefail

ZSHRC="${ZSHRC:-$HOME/.zshrc}"
BEGIN='# >>> agent-harness auto-mode functions >>>'
END='# <<< agent-harness auto-mode functions <<<'
APPLY=0
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
    *) printf 'ERROR: unknown argument: %s\n' "$arg" >&2; exit 2 ;;
  esac
done

read -r -d '' BLOCK <<'EOF' || true
# >>> agent-harness auto-mode functions >>>
# Source: agent-harness/docs/setup.md. Auto Mode keeps the sandbox; never alias
# claude/codex to the fully-bypassing --dangerously-* flags.
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
# <<< agent-harness auto-mode functions <<<
EOF

current=""
[[ -f "$ZSHRC" ]] && current="$(cat "$ZSHRC")"

# Drop any existing marked block (BEGIN..END inclusive), then trailing blanks.
stripped="$(printf '%s\n' "$current" | awk -v b="$BEGIN" -v e="$END" '
  $0==b {skip=1; next}
  $0==e {skip=0; next}
  !skip {print}
' | awk 'NF{n=NR} {a[NR]=$0} END{for(i=1;i<=n;i++)print a[i]}')"

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
