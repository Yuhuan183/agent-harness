#!/usr/bin/env bash
# 將 agent-harness 專案內的配置回寫到全域 (~/.claude, ~/.codex, ~/.agents)。
# 只覆蓋「可攜契約」檔案；機器狀態 (codex config.toml、claude mcp_servers.json、auth、sessions、cache) 一律不碰。
# 用法：
#   scripts/sync.sh          # dry-run，只列出將發生的動作
#   scripts/sync.sh --apply  # 實際執行（先備份到 backups/<timestamp>/）
#   scripts/sync.sh --apply --accept-settings-overwrite  # 明確允許刪除全域額外 settings keys
# 可攜 source -> HOME 目標只定義於 scripts/deployment-manifest.tsv。
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

# 備份既有目標後以 rsync 覆蓋。--links 原樣複製 symlink（相對連結在 $HOME 同構佈局下依然成立）。
SYNCED_SRC=()
SYNCED_DST=()

sync_path() { # $1 = repo 相對來源  $2 = HOME 相對目標
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
    # --force：允許以 symlink 取代既有實體目錄；--delete 清除 repo 已刪的殘留。
    run rsync -a --links --force --delete --delete-excluded \
      "${RSYNC_FILTERS[@]}" "$src" "$(dirname "$dst")/"
  else
    # File mappings may rename the deployment target (contract -> AGENTS/CLAUDE.md).
    run rsync -a --links --force "$src" "$dst"
  fi
}

log "== agent-harness sync (apply=$APPLY) =="

# 保險：全域 settings.json 若含 repo 沒有的 key（如 /config 或手動寫入的本機偏好），
# 覆蓋前提示搬到 settings.local.json（sync 永不碰）。apply 預設中止，除非明確接受覆蓋。
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
    print("WARN: ~/.claude/settings.json 含 repo 沒有的 key 或陣列項目，apply 將覆蓋刪除；本機偏好請搬到 ~/.claude/settings.local.json：")
    for k in extra:
        print(f"  - {k}")
    raise SystemExit(1)
EOF
  if [[ $APPLY -eq 1 && $SETTINGS_EXTRA -eq 1 && $ACCEPT_SETTINGS_OVERWRITE -ne 1 ]]; then
    log "ERROR: 為避免遺失本機設定，已停止 apply；搬移額外 key 或明確加上 --accept-settings-overwrite。"
    exit 1
  fi
fi

# Manifest order keeps shared .agents targets ahead of Claude/Codex symlinks.
while IFS=$'\t' read -r src_rel dst_rel extra; do
  [[ -z "$src_rel" || "$src_rel" == \#* ]] && continue
  sync_path "$src_rel" "$dst_rel"
done < "$MANIFEST"

# Machine state remains deliberately outside the manifest.
log "note: .claude/mcp_servers.json 為機器狀態（含本機路徑），不自動覆蓋；新增 headroom MCP 時手動 merge .claude/examples/headroom-mcp.merge.json。"
log "note: .codex/config.merge.toml 需手動 merge 進 ~/.codex/config.toml（見 DEPLOY.md），不自動覆蓋。"

# --- 驗證 ---
if [[ $APPLY -eq 1 ]]; then
  # skill symlink 可解析
  for l in "$HOME/.claude/skills/headroom-protocol" "$HOME/.codex/skills/headroom-protocol" \
           "$HOME/.claude/skills/speak-human-tw" "$HOME/.codex/skills/speak-human-tw" \
           "$HOME/.claude/skills/experience-ledger" "$HOME/.codex/skills/experience-ledger"; do
    [[ -f "$l/SKILL.md" ]] || { log "ERROR: $l 未能解析到 SKILL.md"; exit 1; }
  done
  # 每個同步路徑與 repo 一致（含 repo 已刪檔案已被移除）
  FAIL=0
  cmp -s "$REPO/.claude/CLAUDE.contract.md" "$HOME/.claude/CLAUDE.md" \
    || { log "ERROR: ~/.claude/CLAUDE.md 與 CLAUDE.contract.md 不一致"; FAIL=1; }
  cmp -s "$REPO/.codex/AGENTS.contract.md" "$HOME/.codex/AGENTS.md" \
    || { log "ERROR: ~/.codex/AGENTS.md 與 AGENTS.contract.md 不一致"; FAIL=1; }
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
      log "ERROR: 同步後仍有差異: ${SYNCED_DST[$i]}"
      log "$diffout"
      FAIL=1
    fi
  done
  [[ $FAIL -eq 0 ]] || exit 1
  # 備份輪替：只保留最近 10 份（apply 已驗證 parity，舊備份僅是回滾保險）
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
  log "done. 全部同步路徑驗證一致；開新 session 驗證契約載入。"
else
  log "dry-run 完成；確認無誤後執行 scripts/sync.sh --apply"
fi
