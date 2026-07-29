#!/usr/bin/env bash
# Points a checkout's git at this repo's tracked hooks (main/claude/githooks),
# which is what turns the tracked pre-commit file into an installed gate.
#
# Split out of sync.sh so both outcomes can be tested against a scratch repo:
# the install itself, and the refusal when core.hooksPath already belongs to
# another tool. Git allows exactly one hooks directory, so a conflict cannot be
# merged - it is reported, left alone, and exits non-zero, because a sync that
# quietly finished without the gate is the failure this exit code exists for.
#
# Usage: install-git-hooks.sh [--dry-run] [repo]
# Exit:  0 installed or already ours   3 core.hooksPath belongs to something else
set -euo pipefail

WANT="main/claude/githooks"
DRY=0
REPO=""
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    *) REPO="$arg" ;;
  esac
done

# An explicit repo argument is a deliberate target and is always acted on. A
# defaulted one is the developer's own checkout, and the suite runs a real
# `sync.sh --apply` as a fixture with REPO pointing here no matter what HOME
# says - the sentinel marks exactly that nested case, where writing repo-local
# config would be a side effect of running the tests.
if [[ -z "$REPO" ]]; then
  REPO="$(cd "$(dirname "$0")/.." && pwd)"
  if [[ "${AGENT_HARNESS_PREFLIGHT_ACTIVE:-0}" == "1" ]]; then
    echo "git hooks: nested run, leaving core.hooksPath alone"
    exit 0
  fi
fi

current="$(git -C "$REPO" config --local --get core.hooksPath || true)"

if [[ "$current" == "$WANT" ]]; then
  echo "git hooks: core.hooksPath already set"
  exit 0
fi

if [[ -n "$current" ]]; then
  echo "ERROR: core.hooksPath is '$current', which this repo did not set."
  echo "       The pre-commit test gate is NOT installed in $REPO."
  echo "       Chain it by hand from '$current/pre-commit', or run"
  echo "       'git -C $REPO config --unset core.hooksPath' and re-run sync."
  exit 3
fi

if [[ $DRY -eq 1 ]]; then
  echo "[dry-run] git -C $REPO config --local core.hooksPath $WANT"
  exit 0
fi

git -C "$REPO" config --local core.hooksPath "$WANT"
echo "git hooks: core.hooksPath -> $WANT (undo: git config --unset core.hooksPath)"
