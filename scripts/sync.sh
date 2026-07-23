#!/usr/bin/env bash
# Syncs config from the agent-harness project back to global (~/.claude, ~/.codex, ~/.agents).
# Only overwrites "portable contract" files; machine state (codex config.toml, claude mcp_servers.json, auth, sessions, cache) is never touched.
# Usage:
#   scripts/sync.sh          # dry-run, only lists the actions that would happen
#   scripts/sync.sh --apply  # actually run it (backs up to backups/<timestamp>/ first)
#   scripts/sync.sh --apply --accept-settings-overwrite  # explicitly allow deleting extra global settings keys
# Portable source -> HOME target mappings are defined only in scripts/deployment-manifest.tsv.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="$REPO/scripts/deployment-manifest.tsv"
APPLY=0
ACCEPT_SETTINGS_OVERWRITE=0
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --accept-settings-overwrite) ACCEPT_SETTINGS_OVERWRITE=1 ;;
    -h|--help)
      sed -n '2,6p' "$0"
      exit 0
      ;;
    *) printf 'ERROR: unknown argument: %s\n' "$arg" >&2; exit 2 ;;
  esac
done
TS="$(date +%Y%m%d-%H%M%S)"
BACKUP="$REPO/backups/$TS"
BACKUP_CREATED=0
RSYNC_FILTERS=(--exclude '__pycache__/' --exclude '*.pyc' --exclude '.DS_Store')

log()  { printf '%s\n' "$*"; }
run()  { if [[ $APPLY -eq 1 ]]; then "$@"; else log "[dry-run] $*"; fi }

validate_manifest() {
  [[ -f "$MANIFEST" ]] || { log "ERROR: missing deployment manifest: $MANIFEST"; return 1; }
  local src_rel dst_rel extra src count=0 seen
  # Empty sentinel keeps Bash 3.2 + nounset from treating an empty array as unbound.
  local seen_sources=("") seen_targets=("")
  while IFS=$'\t' read -r src_rel dst_rel extra; do
    [[ -z "$src_rel" || "$src_rel" == \#* ]] && continue
    if [[ -z "$dst_rel" || -n "$extra" ]]; then
      log "ERROR: malformed deployment manifest row: $src_rel"
      return 1
    fi
    case "$src_rel:$dst_rel" in
      .agents/*:.agents/*|.claude/*:.claude/*|.codex/*:.codex/*) ;;
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
    count=$((count + 1))
  done < "$MANIFEST"
  [[ $count -gt 0 ]] || { log "ERROR: deployment manifest is empty"; return 1; }
}

preflight() {
  log "== preflight =="
  python3 -m json.tool "$REPO/.claude/settings.json" >/dev/null
  python3 -m json.tool "$REPO/.claude/examples/headroom-mcp.merge.json" >/dev/null
  bash -n "$REPO/scripts/sync.sh" "$REPO/.claude/sh/statusline.sh"
  validate_manifest
  "$REPO/.claude/scripts/model-routing" validate >/dev/null
  "$REPO/.claude/scripts/model-routing" check-pins >/dev/null
  "$REPO/.codex/scripts/model-routing" validate >/dev/null
  git -C "$REPO" diff --check
  # Tests exercise sync.sh itself. The sentinel prevents recursive suites while
  # preserving every non-recursive preflight check in nested dry-runs.
  if [[ "${AGENT_HARNESS_PREFLIGHT_ACTIVE:-0}" != "1" ]]; then
    AGENT_HARNESS_PREFLIGHT_ACTIVE=1 PYTHONDONTWRITEBYTECODE=1 \
      python3 -m unittest discover -s "$REPO/.claude/tests" -q
  fi
  log "preflight: passed"
}

preflight

# Back up existing targets, then overwrite via rsync. --links copies symlinks as-is (relative links still hold under the isomorphic $HOME layout).
SYNCED_SRC=()
SYNCED_DST=()

sync_path() { # $1 = repo-relative source  $2 = HOME-relative target
  local src="$REPO/$1" dst_rel="$2" dst="$HOME/$2"
  [[ -e "$src" || -L "$src" ]] || { log "ERROR: missing manifest source: $1"; return 1; }
  SYNCED_SRC+=("$src"); SYNCED_DST+=("$dst")
  if [[ -e "$dst" && $APPLY -eq 1 ]]; then
    mkdir -p "$BACKUP/$(dirname "$dst_rel")"
    cp -R "$dst" "$BACKUP/$dst_rel"
    BACKUP_CREATED=1
  fi
  run mkdir -p "$(dirname "$dst")"
  if [[ -d "$src" ]]; then
    # --force: allows a symlink to replace an existing real directory; --delete clears leftovers already removed from the repo.
    run rsync -a --links --force --delete --delete-excluded \
      "${RSYNC_FILTERS[@]}" "$src" "$(dirname "$dst")/"
  else
    # File mappings may rename the deployment target (contract -> AGENTS/CLAUDE.md).
    run rsync -a --links --force "$src" "$dst"
  fi
}

log "== agent-harness sync (apply=$APPLY) =="

# Safety net: if the global settings.json has keys the repo doesn't (e.g. from /config or manually added local preferences),
# warn before overwriting and suggest moving them to settings.local.json (sync never touches that file). apply aborts by default unless overwrite is explicitly accepted.
if [[ -f "$HOME/.claude/settings.json" ]]; then
  SETTINGS_EXTRA=0
  python3 - "$REPO/.claude/settings.json" "$HOME/.claude/settings.json" <<'EOF' || SETTINGS_EXTRA=1
import json, sys
repo = json.load(open(sys.argv[1])); glb = json.load(open(sys.argv[2]))
def extra_values(a, b, prefix=""):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in b:
            path = f"{prefix}.{k}" if prefix else k
            if k not in a:
                out.append(path)
            else:
                out.extend(extra_values(a[k], b[k], path))
    elif isinstance(a, list) and isinstance(b, list):
        # Settings arrays are semantically collections. Preserve every global
        # entry not represented in the portable repo contract, independent of
        # ordering; canonical JSON also handles hook objects safely.
        available = [json.dumps(item, sort_keys=True, separators=(",", ":"))
                     for item in a]
        for index, item in enumerate(b):
            encoded = json.dumps(item, sort_keys=True, separators=(",", ":"))
            if encoded in available:
                available.remove(encoded)
            else:
                out.append(f"{prefix}[{index}]")
    elif type(a) is not type(b):
        out.append(f"{prefix} (type differs)")
    return out
extra = extra_values(repo, glb)
if extra:
    print("WARN: ~/.claude/settings.json has keys or array items not present in the repo; apply would overwrite/delete them. Move local preferences to ~/.claude/settings.local.json:")
    for k in extra:
        print(f"  - {k}")
    raise SystemExit(1)
EOF
  if [[ $APPLY -eq 1 && $SETTINGS_EXTRA -eq 1 && $ACCEPT_SETTINGS_OVERWRITE -ne 1 ]]; then
    log "ERROR: apply stopped to avoid losing local settings; move the extra keys or explicitly pass --accept-settings-overwrite."
    exit 1
  fi
fi

# Manifest order keeps shared .agents targets ahead of Claude/Codex symlinks.
# settings.json rows are deferred to a second pass regardless of manifest
# position: hooks activate the moment settings land, so every file a hook
# entry references (hooks/, scripts/) must already be deployed. Applying
# settings first opens a window where a registered hook cannot be found and
# every guarded tool call errors out (observed 2026-07-23).
DEFERRED_SETTINGS_ROWS=("")
while IFS=$'\t' read -r src_rel dst_rel extra; do
  [[ -z "$src_rel" || "$src_rel" == \#* ]] && continue
  if [[ "$(basename "$dst_rel")" == "settings.json" ]]; then
    DEFERRED_SETTINGS_ROWS+=("$src_rel"$'\t'"$dst_rel")
    continue
  fi
  sync_path "$src_rel" "$dst_rel"
done < "$MANIFEST"
for row in "${DEFERRED_SETTINGS_ROWS[@]}"; do
  [[ -z "$row" ]] && continue
  IFS=$'\t' read -r src_rel dst_rel <<< "$row"
  sync_path "$src_rel" "$dst_rel"
done

# Machine state remains deliberately outside the manifest.
log "note: .claude/mcp_servers.json is machine state (contains local paths) and is not auto-overwritten; when adding the headroom MCP, manually merge .claude/examples/headroom-mcp.merge.json."
log "note: .codex/config.merge.toml must be manually merged into ~/.codex/config.toml (see DEPLOY.md); it is not auto-overwritten."

# --- Verification ---
if [[ $APPLY -eq 1 ]]; then
  # skill symlinks resolve
  for l in "$HOME/.claude/skills/headroom-protocol" "$HOME/.codex/skills/headroom-protocol" \
           "$HOME/.claude/skills/speak-human-tw" "$HOME/.codex/skills/speak-human-tw" \
           "$HOME/.claude/skills/experience-ledger" "$HOME/.codex/skills/experience-ledger"; do
    [[ -f "$l/SKILL.md" ]] || { log "ERROR: $l failed to resolve to SKILL.md"; exit 1; }
  done
  # Every synced path matches the repo (including removal of files already deleted from the repo)
  FAIL=0
  cmp -s "$REPO/.claude/CLAUDE.contract.md" "$HOME/.claude/CLAUDE.md" \
    || { log "ERROR: ~/.claude/CLAUDE.md does not match CLAUDE.contract.md"; FAIL=1; }
  cmp -s "$REPO/.codex/AGENTS.contract.md" "$HOME/.codex/AGENTS.md" \
    || { log "ERROR: ~/.codex/AGENTS.md does not match AGENTS.contract.md"; FAIL=1; }
  for i in "${!SYNCED_SRC[@]}"; do
    if [[ -d "${SYNCED_SRC[$i]}" ]]; then
      diffout="$(rsync -an --links --force --delete --delete-excluded \
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
  [[ $FAIL -eq 0 ]] || exit 1
  # Backup rotation: keep only the most recent 10 (apply already verified parity; old backups are just a rollback safety net)
  if [[ -d "$REPO/backups" ]]; then
    find "$REPO/backups" -mindepth 1 -maxdepth 1 -type d -print \
      | sort -r | tail -n +11 | while read -r old; do
        rm -rf "$old"
      done
  fi
  if [[ $BACKUP_CREATED -eq 1 ]]; then
    log "backup: $BACKUP"
  else
    log "backup: none (no existing managed targets)"
  fi
  log "done. All synced paths verified consistent; open a new session to verify contract loading."
else
  log "dry-run complete; once confirmed, run scripts/sync.sh --apply"
fi
