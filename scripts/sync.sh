#!/usr/bin/env bash
# Syncs config from the agent-harness project back to global (~/.claude, ~/.codex, ~/.agents).
# Only overwrites portable contract files; machine state (Codex config.toml, Claude Code ~/.claude.json MCP entries, auth, sessions, cache) is never touched.
# Usage:
#   scripts/sync.sh          # dry-run, only lists the actions that would happen
#   scripts/sync.sh --apply  # actually run it
#   scripts/sync.sh --apply --accept-contract-takeover   # explicitly allow overwriting a pre-existing foreign AGENTS.md/CLAUDE.md
# Portable source -> HOME target mappings are defined only in scripts/deployment-manifest.tsv.
#
# `sh scripts/sync.sh` is bash 3.2 in POSIX mode on macOS, which disables the
# process substitution the deployment inventory is read with. bash parses as it
# executes, so that failure lands mid-run - after the git hook is installed and
# preflight has reported success - instead of up front. Hand the script to real
# bash before the parser ever reaches the construct.
#
# POSIX-mode bash still sets BASH_VERSION, so the name of the shell does not
# answer the question; the construct itself is tested, inside an eval so this
# file still parses where it is unsupported. SHELLOPTS is dropped because an
# inherited `posix` would send the re-exec straight back here.
if [ -z "${BASH_VERSION:-}" ] || ! (eval ': < <(:)') 2>/dev/null; then
  exec env -u SHELLOPTS bash "$0" "$@"
fi
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="$REPO/scripts/deployment-manifest.tsv"
PYTHON_RUN="$REPO/main/.agents/scripts/python3-run"
PYTHON_SHIM_DIR=""
APPLY=0
ACCEPT_CONTRACT_TAKEOVER=0
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --accept-contract-takeover) ACCEPT_CONTRACT_TAKEOVER=1 ;;
    -h|--help)
      sed -n '2,7p' "$0"
      exit 0
      ;;
    *) printf 'ERROR: unknown argument: %s\n' "$arg" >&2; exit 2 ;;
  esac
done
RSYNC_FILTERS=(--exclude '__pycache__/' --exclude '*.pyc' --exclude '.DS_Store')

log()  { printf '%s\n' "$*"; }
run()  { if [[ $APPLY -eq 1 ]]; then "$@"; else log "[dry-run] $*"; fi }

cleanup_python_shim() {
  [[ -n "$PYTHON_SHIM_DIR" ]] || return 0
  rm -f "$PYTHON_SHIM_DIR/python3"
  rmdir "$PYTHON_SHIM_DIR"
}

sync_cleanup() {
  local status=$?
  cleanup_python_shim
  [[ -n "${DEPLOY_STATE_NEW:-}" ]] && rm -f "$DEPLOY_STATE_NEW"
  # An abort that never ran a failing command - a parse error in a function the
  # reader had not reached yet is the one that actually happened - leaves $? at
  # 0, and bash exits with whatever this trap leaves behind. Preserving $? is
  # therefore not enough: reaching the last line is the only success signal, so
  # anything short of that is reported as failure rather than as a clean sync.
  if [[ $status -eq 0 && $SYNC_COMPLETED -eq 0 ]]; then
    log "ERROR: sync stopped before finishing; nothing below the failure ran."
    return 1
  fi
  return "$status"
}

prepare_python_path() {
  local python_executable
  python_executable="$("$PYTHON_RUN" -c 'import sys; print(sys.executable)')" || return 1
  PYTHON_SHIM_DIR="$(mktemp -d "${TMPDIR:-/tmp}/agent-harness-python.XXXXXX")"
  ln -s "$python_executable" "$PYTHON_SHIM_DIR/python3"
  PATH="$PYTHON_SHIM_DIR:$PATH"
  export PATH
}

validate_manifest() {
  [[ -f "$MANIFEST" ]] || { log "ERROR: missing deployment manifest: $MANIFEST"; return 1; }
  local src_rel dst_rel mode extra src count=0 seen
  # Empty sentinel keeps Bash 3.2 + nounset from treating an empty array as unbound.
  local seen_sources=("") seen_targets=("")
  while IFS=$'\t' read -r src_rel dst_rel mode extra; do
    [[ -z "$src_rel" || "$src_rel" == \#* ]] && continue
    if [[ -z "$dst_rel" || -n "$extra" \
          || ( -n "$mode" && "$mode" != "merge" && "$mode" != "merge-json" \
               && "$mode" != "merge-toml" ) ]]; then
      log "ERROR: malformed deployment manifest row: $src_rel"
      return 1
    fi
    if [[ "$mode" == "merge" \
          && "$src_rel:$dst_rel" != "main/.agents/skills:.agents/skills" ]]; then
      log "ERROR: merge mode is restricted to the shared skill root: $src_rel -> $dst_rel"
      return 1
    fi
    # merge-json exists for one file: settings.json has three writers (this
    # repo, Claude Code's /model and /effort, third-party hook installers), so
    # a wholesale copy would delete two of them.
    if [[ "$mode" == "merge-json" \
          && "$src_rel:$dst_rel" != "main/claude/settings.json:.claude/settings.json" ]]; then
      log "ERROR: merge-json mode is restricted to Claude settings: $src_rel -> $dst_rel"
      return 1
    fi
    # merge-toml exists for one file: ~/.codex/config.toml carries GPT model
    # and effort, MCP, plugins, marketplaces, desktop, shell policy, and
    # per-project trust alongside the agent registrations this repo owns.
    if [[ "$mode" == "merge-toml" \
          && "$src_rel:$dst_rel" != "main/codex/config.merge.toml:.codex/config.toml" ]]; then
      log "ERROR: merge-toml mode is restricted to Codex config: $src_rel -> $dst_rel"
      return 1
    fi
    case "$src_rel:$dst_rel" in
      main/.agents/*:.agents/*|main/claude/*:.claude/*|main/codex/*:.codex/*) ;;
      *) log "ERROR: unsafe deployment mapping: $src_rel -> $dst_rel"; return 1 ;;
    esac
    case "/$src_rel/:/$dst_rel/" in
      *"/../"*|*"/./"*|*"//"*)
        log "ERROR: unsafe deployment path: $src_rel -> $dst_rel"; return 1 ;;
    esac
    for seen in "${seen_sources[@]}"; do
      [[ "$seen" != "$src_rel" ]] \
        || { log "ERROR: duplicate deployment source: $src_rel"; return 1; }
    done
    for seen in "${seen_targets[@]}"; do
      [[ "$seen" != "$dst_rel" ]] \
        || { log "ERROR: duplicate deployment target: $dst_rel"; return 1; }
    done
    seen_sources+=("$src_rel"); seen_targets+=("$dst_rel")
    src="$REPO/$src_rel"
    [[ -e "$src" || -L "$src" ]] \
      || { log "ERROR: deployment source missing: $src_rel"; return 1; }
    if [[ "$mode" == "merge" ]]; then
      validate_project_skill_inventory "$src"
    fi
    count=$((count + 1))
  done < "$MANIFEST"
  [[ $count -gt 0 ]] || { log "ERROR: deployment manifest is empty"; return 1; }
}

validate_project_skill_inventory() {
  local root="$1" inventory="$1/INSTALLED.txt" name seen="" entry
  [[ -f "$inventory" ]] \
    || { log "ERROR: missing project skill inventory: $inventory"; return 1; }
  while IFS= read -r name || [[ -n "$name" ]]; do
    [[ "$name" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]] \
      || { log "ERROR: invalid project skill name in INSTALLED.txt: $name"; return 1; }
    for entry in $seen; do
      [[ "$entry" != "$name" ]] \
        || { log "ERROR: duplicate project skill in INSTALLED.txt: $name"; return 1; }
    done
    [[ -f "$root/$name/SKILL.md" ]] \
      || { log "ERROR: listed project skill is missing SKILL.md: $name"; return 1; }
    seen="$seen $name"
  done < "$inventory"
  [[ -n "$seen" ]] || { log "ERROR: project skill inventory is empty"; return 1; }
  for entry in "$root"/*; do
    [[ -d "$entry" && -f "$entry/SKILL.md" ]] || continue
    name="$(basename "$entry")"
    grep -Fxq "$name" "$inventory" \
      || { log "ERROR: project skill missing from INSTALLED.txt: $name"; return 1; }
  done
}

# The commit gate's other half. The Bash hook decides before the shell runs the
# command and therefore has to infer the target from text; this points git at a
# tracked hooks directory, so a commit in *this* checkout goes through the same
# check whatever the command looked like. The installer is a separate script so
# both of its outcomes are testable against a scratch repo; a non-zero status
# means this deployment does not have the gate.
GIT_HOOK_STATUS=0
install_git_hooks() {
  # Spelled out rather than built as an array: under `set -u`, bash 3.2 (which
  # is what /usr/bin/env bash is on macOS) treats an empty "${args[@]}" as
  # unbound and kills the whole sync.
  if [[ $APPLY -eq 1 ]]; then
    "$REPO/scripts/install-git-hooks.sh" || GIT_HOOK_STATUS=$?
  else
    "$REPO/scripts/install-git-hooks.sh" --dry-run || GIT_HOOK_STATUS=$?
  fi
}

preflight() {
  log "== preflight =="
  # Use the same portable Python 3.11+ selector as deployed routing entrypoints.
  prepare_python_path \
    || { log "ERROR: portable Python 3.11+ runtime unavailable"; return 1; }
  "$PYTHON_RUN" -m json.tool "$REPO/main/claude/settings.json" >/dev/null
  # Every hook group in the repo must be recognisably ours, or merge-json could
  # not update it on deploy and it would silently fossilise.
  "$PYTHON_RUN" "$REPO/scripts/merge-settings.py" \
    "$REPO/main/claude/settings.json" --check >/dev/null
  "$PYTHON_RUN" -m json.tool "$REPO/main/claude/examples/headroom-mcp.legacy.json" >/dev/null
  bash -n "$REPO/scripts/sync.sh" "$REPO/main/claude/sh/statusline.sh"
  validate_manifest
  "$REPO/main/claude/scripts/model-routing" validate >/dev/null
  "$REPO/main/claude/scripts/model-routing" check-pins >/dev/null
  "$REPO/main/codex/scripts/model-routing" validate >/dev/null
  git -C "$REPO" diff --check
  # Tests exercise sync.sh itself. The sentinel prevents recursive suites while
  # preserving every non-recursive preflight check in nested dry-runs.
  if [[ "${AGENT_HARNESS_PREFLIGHT_ACTIVE:-0}" != "1" ]]; then
    AGENT_HARNESS_PREFLIGHT_ACTIVE=1 PYTHONDONTWRITEBYTECODE=1 \
      "$PYTHON_RUN" -m unittest discover -s "$REPO/main/claude/tests" -q
  fi
  log "preflight: passed"
}

SYNC_COMPLETED=0
trap sync_cleanup EXIT
preflight
install_git_hooks

# Overwrite targets via rsync. --links copies symlinks inside shared entries and
# platform wrappers as-is; relative links still hold because the shared root
# keeps the same name and depth in the repo as in $HOME.
#
# No backup is taken. Every deployed byte is tracked in git, so a rollback is
# `git checkout <ref> && scripts/sync.sh --apply`, and apply already refuses to
# overwrite a contract this repo never produced. A second copy under the repo
# only added rotation logic and trees for the CLIs to discover.
SYNCED_SRC=()
SYNCED_DST=()
# Merged targets are verified by re-merge idempotence, not byte parity: a
# merged file legitimately carries machine keys the source does not have.
MERGED_SRC=()
MERGED_DST=()
MERGED_TOOL=()

# Per-file deployment inventory. Several manifest targets are shared
# namespaces rather than this repo's territory: ~/.claude/hooks, ~/.claude/
# agents, ~/.claude/scripts and ~/.codex/prompts are where third-party
# installers put their own files too. A directory-wide `rsync --delete`
# removed those as "leftovers already deleted from the repo" — the same
# ownership error that let a vendor hook be dropped from settings.json.
# Deleting is therefore driven by what this repo deployed last time, recorded
# here, rather than by what happens to be in the directory now.
DEPLOY_STATE="$HOME/.agents/.deployed-files.tsv"
DEPLOY_STATE_NEW="$(mktemp "${TMPDIR:-/tmp}/agent-harness-deployed.XXXXXX")"
PRUNED=()

cleanup_deploy_state() { rm -f "$DEPLOY_STATE_NEW"; }

# Every HOME-relative path a manifest source contributes. Mirrors
# RSYNC_FILTERS: bytecode and .DS_Store are never deployed, so they are never
# owned either. A symlinked source deploys as one symlink, so it is one entry —
# walking into it would claim the shared tree it points at.
repo_owned_entries() { # $1 = source path  $2 = HOME-relative target
  if [[ -L "$1" ]]; then
    printf '%s\n' "$2"
    return
  fi
  (cd "$1" && find . \( -name '__pycache__' -o -name '*.pyc' -o -name '.DS_Store' \) \
      -prune -o \( -type f -o -type l \) -print) \
    | sed -e "s|^\./|$2/|" | LC_ALL=C sort
}

# Files this repo deployed under a target root on the previous run.
previously_deployed() { # $1 = HOME-relative target root
  [[ -f "$DEPLOY_STATE" ]] || return 0
  awk -F'\t' -v root="$1" '$1 == root { print $2 }' "$DEPLOY_STATE"
}

# Remove exactly what this repo deployed before and no longer ships. A file it
# never deployed is someone else's and is left alone, even inside a directory
# every other file of which is ours.
prune_retired_files() { # $1 = HOME-relative target root  $2 = current entry list
  local root="$1" current="$2" base="$3" rel dir
  while IFS= read -r rel; do
    [[ -n "$rel" ]] || continue
    grep -Fxq "$rel" "$current" && continue
    [[ -e "$base/$rel" || -L "$base/$rel" ]] || continue
    PRUNED+=("$base/$rel")
    run rm -f "$base/$rel"
    # Take the directories emptied along with it, never a foreign one: rmdir
    # refuses a directory that still holds anything.
    if [[ $APPLY -eq 1 ]]; then
      dir="$(dirname "$rel")"
      while [[ "$dir" != "." && "$dir" != "/" ]]; do
        rmdir "$base/$dir" 2>/dev/null || break
        dir="$(dirname "$dir")"
      done
    fi
  done < <(previously_deployed "$root")
}

sync_skill_root() { # $1 = repo-relative skill root  $2 = HOME-relative skill root
  local src="$REPO/$1" dst_rel="$2" dst="$HOME/$2" name child_src child_dst child_rel source_marker
  validate_project_skill_inventory "$src"
  run mkdir -p "$dst"
  while IFS= read -r name || [[ -n "$name" ]]; do
    child_src="$src/$name"
    child_dst="$dst/$name"
    child_rel="$dst_rel/$name"
    SYNCED_SRC+=("$child_src"); SYNCED_DST+=("$child_dst")
    run rsync -a --links --force --delete --delete-excluded \
      "${RSYNC_FILTERS[@]}" "$child_src" "$dst/"
  done < "$src/INSTALLED.txt"

  SYNCED_SRC+=("$src/INSTALLED.txt"); SYNCED_DST+=("$dst/INSTALLED.txt")
  run rsync -a --links --force "$src/INSTALLED.txt" "$dst/INSTALLED.txt"

  # Machine-local provenance lets maintenance tools find the authoritative
  # checkout instead of editing a deployed copy that the next sync replaces.
  source_marker="$dst/.agent-harness-source"
  if [[ $APPLY -eq 1 ]]; then
    printf '%s\n' "$REPO" > "$source_marker"
  else
    log "[dry-run] write source checkout $REPO -> $source_marker"
  fi
}

sync_path() { # $1 = repo-relative source  $2 = HOME-relative target  $3 = optional mode
  local src="$REPO/$1" dst_rel="$2" mode="${3:-}" dst="$HOME/$2"
  [[ -e "$src" || -L "$src" ]] || { log "ERROR: missing manifest source: $1"; return 1; }
  if [[ "$mode" == "merge" ]]; then
    sync_skill_root "$1" "$2"
    return
  fi
  if [[ "$mode" == "merge-json" || "$mode" == "merge-toml" ]]; then
    local merger="merge-settings.py"
    [[ "$mode" == "merge-toml" ]] && merger="merge-toml.py"
    MERGED_SRC+=("$src"); MERGED_DST+=("$dst"); MERGED_TOOL+=("$merger")
    if [[ $APPLY -eq 1 ]]; then
      mkdir -p "$(dirname "$dst")"
      "$PYTHON_RUN" "$REPO/scripts/$merger" "$src" "$dst"
    else
      "$PYTHON_RUN" "$REPO/scripts/$merger" "$src" "$dst" --dry-run
    fi
    return
  fi
  SYNCED_SRC+=("$src"); SYNCED_DST+=("$dst")
  run mkdir -p "$(dirname "$dst")"
  if [[ -d "$src" ]]; then
    # --force allows a symlink to replace an existing real directory. There is
    # deliberately no --delete: the deployed directory may be a shared
    # namespace, so leftovers are retired from the per-file inventory below
    # instead of by "everything here that is not in the source".
    local entries
    entries="$(mktemp "${TMPDIR:-/tmp}/agent-harness-entries.XXXXXX")"
    repo_owned_entries "$src" "$dst_rel" > "$entries"
    prune_retired_files "$dst_rel" "$entries" "$HOME"
    awk -v root="$dst_rel" '{ print root "\t" $0 }' "$entries" >> "$DEPLOY_STATE_NEW"
    rm -f "$entries"
    run rsync -a --links --force \
      "${RSYNC_FILTERS[@]}" "$src" "$(dirname "$dst")/"
  else
    # File mappings may rename the deployment target (contract -> AGENTS/CLAUDE.md).
    run rsync -a --links --force "$src" "$dst"
  fi
}

log "== agent-harness sync (apply=$APPLY) =="

# settings.json is deployed with merge-json, so extra global keys and foreign
# hook groups survive by construction and no overwrite escape hatch is needed;
# scripts/merge-settings.py reports exactly what it preserved on each run.

# First-takeover guard: the contract-file mappings (CLAUDE.md / AGENTS.md
# targets) fully replace the deployed file. A pre-existing target whose content
# never appeared in this repo's history is someone else's guidance, not a stale
# copy of ours — never overwrite it silently; require explicit takeover.
FOREIGN_CONTRACTS=("")
while IFS=$'\t' read -r src_rel dst_rel extra; do
  [[ -z "$src_rel" || "$src_rel" == \#* ]] && continue
  case "$(basename "$dst_rel")" in CLAUDE.md|AGENTS.md) ;; *) continue ;; esac
  dst="$HOME/$dst_rel"
  [[ -s "$dst" ]] || continue
  cmp -s "$REPO/$src_rel" "$dst" && continue
  dst_hash="$(git -C "$REPO" hash-object "$dst")"
  legacy_src_rel="${src_rel#main/}"
  # Collect first, match second. Piping straight into `grep -q` lets grep exit
  # on the first hit, SIGPIPE the rev-list still feeding it, and surface as 141
  # under `pipefail` — which marked every legitimate contract update as foreign
  # content and stopped apply. The guard only ever passed when the deployed file
  # already matched the worktree, i.e. when there was nothing to deploy.
  # Contract sources have moved twice: out of the repo root into main/, then
  # from main/.claude to main/claude so neither CLI discovers the source tree.
  # `rev-list -- <path>` only sees a blob under the path it had in that commit,
  # so every historical location has to be asked, or a machine deployed from an
  # older checkout reads as someone else's guidance.
  dotted_src_rel="${src_rel/#main\//main/.}"
  history_objects="$(
    git -C "$REPO" rev-list --all --objects -- "$src_rel"
    git -C "$REPO" rev-list --all --objects -- "$legacy_src_rel"
    git -C "$REPO" rev-list --all --objects -- "$dotted_src_rel"
  )"
  grep -q "^$dst_hash " <<<"$history_objects" || FOREIGN_CONTRACTS+=("$dst_rel")
done < "$MANIFEST"
for dst_rel in "${FOREIGN_CONTRACTS[@]}"; do
  [[ -z "$dst_rel" ]] && continue
  log "WARN: ~/$dst_rel has content unknown to this repo; apply would replace it."
done
if [[ $APPLY -eq 1 && ${#FOREIGN_CONTRACTS[@]} -gt 1 && $ACCEPT_CONTRACT_TAKEOVER -ne 1 ]]; then
  log "ERROR: apply stopped to avoid overwriting a contract file this repo never produced; merge the existing guidance manually or explicitly pass --accept-contract-takeover."
  exit 1
fi

# Manifest order keeps shared .agents targets ahead of Claude/Codex symlinks.
# settings.json rows are deferred to a second pass regardless of manifest
# position: hooks activate the moment settings land, so every file a hook
# entry references (hooks/, scripts/) must already be deployed. Applying
# settings first opens a window where a registered hook cannot be found and
# every guarded tool call errors out (observed 2026-07-23).
DEFERRED_SETTINGS_ROWS=("")
while IFS=$'\t' read -r src_rel dst_rel mode extra; do
  [[ -z "$src_rel" || "$src_rel" == \#* ]] && continue
  if [[ "$(basename "$dst_rel")" == "settings.json" ]]; then
    DEFERRED_SETTINGS_ROWS+=("$src_rel"$'\t'"$dst_rel"$'\t'"$mode")
    continue
  fi
  sync_path "$src_rel" "$dst_rel" "$mode"
done < "$MANIFEST"
for row in "${DEFERRED_SETTINGS_ROWS[@]}"; do
  [[ -z "$row" ]] && continue
  IFS=$'\t' read -r src_rel dst_rel mode <<< "$row"
  sync_path "$src_rel" "$dst_rel" "$mode"
done

# Record what this run deployed, so the next one can retire exactly the files
# this repo dropped. Absent inventory means unknown, never foreign: the first
# run after this mechanism landed prunes nothing, which is the safe direction.
if [[ $APPLY -eq 1 ]]; then
  mkdir -p "$(dirname "$DEPLOY_STATE")"
  LC_ALL=C sort -o "$DEPLOY_STATE_NEW" "$DEPLOY_STATE_NEW"
  mv "$DEPLOY_STATE_NEW" "$DEPLOY_STATE"
  DEPLOY_STATE_NEW=""
elif [[ ! -f "$DEPLOY_STATE" ]]; then
  log "note: no deployment inventory at ~/.agents/.deployed-files.tsv yet; the first --apply records one and later runs retire files this repo drops."
fi
for path in "${PRUNED[@]:-}"; do
  [[ -z "$path" ]] && continue
  log "retired (repo no longer ships it): ${path#$HOME/}"
done

# Machine state remains deliberately outside the manifest.
log "note: Claude Code MCP state lives in ~/.claude.json and is not auto-overwritten; add Headroom with 'headroom mcp install --agent claude --proxy-url http://127.0.0.1:8787'."
log "note: ~/.codex/config.toml is merged section-scoped ([agents] only, see DEPLOY.md); GPT model/effort, MCP, plugins, desktop, and project trust are preserved, never authored here."

# --- Verification ---
if [[ $APPLY -eq 1 ]]; then
  # Shared skill symlinks and platform wrappers resolve to SKILL.md.
  for l in "$HOME/.claude/skills/headroom-protocol" "$HOME/.codex/skills/headroom-protocol" \
           "$HOME/.claude/skills/speak-human-tw" "$HOME/.codex/skills/speak-human-tw" \
           "$HOME/.claude/skills/experience-ledger" "$HOME/.codex/skills/experience-ledger" \
           "$HOME/.claude/skills/task-observer" "$HOME/.codex/skills/task-observer"; do
    [[ -f "$l/SKILL.md" ]] || { log "ERROR: $l failed to resolve to SKILL.md"; exit 1; }
  done
  # Every synced path matches the repo (including removal of files already deleted from the repo)
  FAIL=0
  cmp -s "$REPO/main/claude/CLAUDE.contract.md" "$HOME/.claude/CLAUDE.md" \
    || { log "ERROR: ~/.claude/CLAUDE.md does not match CLAUDE.contract.md"; FAIL=1; }
  cmp -s "$REPO/main/codex/AGENTS.contract.md" "$HOME/.codex/AGENTS.md" \
    || { log "ERROR: ~/.codex/AGENTS.md does not match AGENTS.contract.md"; FAIL=1; }
  [[ -f "$HOME/.agents/skills/.agent-harness-source" \
        && "$(<"$HOME/.agents/skills/.agent-harness-source")" == "$REPO" ]] \
    || { log "ERROR: ~/.agents/skills/.agent-harness-source does not identify this checkout"; FAIL=1; }
  for i in "${!SYNCED_SRC[@]}"; do
    if [[ -d "${SYNCED_SRC[$i]}" ]]; then
      # Present and identical, not "the only thing there": a shared namespace
      # legitimately holds another installer's files, and --delete here would
      # report them as drift the way --delete on apply used to remove them.
      # Files this repo retired are checked separately, below.
      diffout="$(rsync -an --links --force \
        "${RSYNC_FILTERS[@]}" --itemize-changes "${SYNCED_SRC[$i]}" "$(dirname "${SYNCED_DST[$i]}")/")"
    else
      if cmp -s "${SYNCED_SRC[$i]}" "${SYNCED_DST[$i]}"; then
        diffout=""
      else
        diffout="file content differs"
      fi
    fi
    if [[ -n "$diffout" ]]; then
      log "ERROR: still differs after sync: ${SYNCED_DST[$i]}"
      log "$diffout"
      FAIL=1
    fi
  done
  for i in "${!MERGED_DST[@]}"; do
    if ! "$PYTHON_RUN" "$REPO/scripts/${MERGED_TOOL[$i]}" \
        "${MERGED_SRC[$i]}" "${MERGED_DST[$i]}" --verify >/dev/null; then
      log "ERROR: merged target still missing repo settings: ${MERGED_DST[$i]}"
      FAIL=1
    fi
  done
  # Retirement is the half the parity rsync no longer covers.
  for path in "${PRUNED[@]:-}"; do
    [[ -z "$path" ]] && continue
    if [[ -e "$path" || -L "$path" ]]; then
      log "ERROR: retired file still deployed: $path"
      FAIL=1
    fi
  done
  [[ $FAIL -eq 0 ]] || exit 1
  log "done. All synced paths verified consistent; open a new session to verify contract loading."
else
  log "dry-run complete; once confirmed, run scripts/sync.sh --apply"
fi

# The file copying is real work and stays done. But a deployment that could not
# install the commit gate is a deployment without the commit gate, and the only
# thing a caller reads is the exit status - reporting success here is how a
# missing boundary becomes invisible until someone commits red.
if [[ $GIT_HOOK_STATUS -ne 0 ]]; then
  log "ERROR: files are deployed, but the git-side commit gate is not installed (see above)."
  exit $GIT_HOOK_STATUS
fi

# Read by sync_cleanup. Every other exit from here on is already non-zero, so
# this line is what separates a finished run from an interrupted one.
SYNC_COMPLETED=1
