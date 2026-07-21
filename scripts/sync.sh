#!/usr/bin/env bash
# 將 agent-harness 專案內的配置回寫到全域 (~/.claude, ~/.codex, ~/.agents)。
# 只覆蓋「可攜契約」檔案；機器狀態 (codex config.toml、claude mcp_servers.json、auth、sessions、cache) 一律不碰。
# 用法：
#   scripts/sync.sh          # dry-run，只列出將發生的動作
#   scripts/sync.sh --apply  # 實際執行（先備份到 backups/<timestamp>/）
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
APPLY=0
[[ "${1:-}" == "--apply" ]] && APPLY=1
TS="$(date +%Y%m%d-%H%M%S)"
BACKUP="$REPO/backups/$TS"

log()  { printf '%s\n' "$*"; }
run()  { if [[ $APPLY -eq 1 ]]; then "$@"; else log "[dry-run] $*"; fi }

# 備份既有目標後以 rsync 覆蓋。--links 原樣複製 symlink（相對連結在 $HOME 同構佈局下依然成立）。
SYNCED_SRC=()
SYNCED_DST=()

sync_path() { # $1 = repo 相對來源  $2 = 全域目標
  local src="$REPO/$1" dst="$2"
  [[ -e "$src" ]] || { log "skip (missing in repo): $1"; return; }
  SYNCED_SRC+=("$src"); SYNCED_DST+=("$dst")
  if [[ -e "$dst" && $APPLY -eq 1 ]]; then
    mkdir -p "$BACKUP/$(dirname "$1")"
    cp -R "$dst" "$BACKUP/$1"
  fi
  run mkdir -p "$(dirname "$dst")"
  # --force：允許以 symlink 取代既有實體目錄（如 ~/.codex/skills/headroom-protocol）
  # --delete：每個同步路徑內以 repo 為準，移除 repo 已刪的殘留（apply 前已備份，可回滾）
  run rsync -a --links --force --delete "$src" "$(dirname "$dst")/"
}

log "== agent-harness sync (apply=$APPLY) =="

# 保險：全域 settings.json 若含 repo 沒有的 key（如 /config 或手動寫入的本機偏好），
# 覆蓋前警告並提示搬到 settings.local.json（sync 永不碰）。只警告，不中止。
if [[ -f "$HOME/.claude/settings.json" ]]; then
  python3 - "$REPO/.claude/settings.json" "$HOME/.claude/settings.json" <<'EOF' || true
import json, sys
repo = json.load(open(sys.argv[1])); glb = json.load(open(sys.argv[2]))
def extra_keys(a, b, prefix=""):
    out = []
    for k in b:
        path = f"{prefix}.{k}" if prefix else k
        if k not in a:
            out.append(path)
        elif isinstance(b[k], dict) and isinstance(a[k], dict):
            out.extend(extra_keys(a[k], b[k], path))
    return out
extra = extra_keys(repo, glb)
if extra:
    print("WARN: ~/.claude/settings.json 含 repo 沒有的 key，apply 將覆蓋刪除；本機偏好請搬到 ~/.claude/settings.local.json：")
    for k in extra:
        print(f"  - {k}")
EOF
fi

# --- .agents：共用 skill 本體與跨 agent 知識先到位（symlink 目標） ---
sync_path ".agents/skills/headroom-protocol" "$HOME/.agents/skills/headroom-protocol"
sync_path ".agents/skills/speak-human-tw"    "$HOME/.agents/skills/speak-human-tw"
sync_path ".agents/skills/experience-ledger" "$HOME/.agents/skills/experience-ledger"
sync_path ".agents/.skill-lock.json"         "$HOME/.agents/.skill-lock.json"
sync_path ".agents/docs"                      "$HOME/.agents/docs"
sync_path ".agents/README.md"                 "$HOME/.agents/README.md"

# --- .claude：可攜契約（mcp_servers.json 為機器狀態，僅提示手動 merge） ---
for p in CLAUDE.md README.md RTK.md settings.json model-routing.toml \
         agents hooks prompts scripts sh tests examples; do
  sync_path ".claude/$p" "$HOME/.claude/$p"
done
log "note: .claude/mcp_servers.json 為機器狀態（含本機路徑），不自動覆蓋；新增 headroom MCP 時手動 merge .claude/examples/headroom-mcp.merge.json。"
sync_path ".claude/plans/orchestration-plan.md" "$HOME/.claude/plans/orchestration-plan.md"
# 自有 skills（逐個列，避免動到全域其他已安裝 skill 與 lark symlinks）
for s in baton-dispatch provider-routing headroom-protocol speak-human-tw experience-ledger; do
  sync_path ".claude/skills/$s" "$HOME/.claude/skills/$s"
done

# --- .codex：可攜契約（config.toml 為機器狀態，僅提示手動 merge） ---
for p in AGENTS.md README.md ANALYSIS.md DEPLOY.md model-routing.toml prompts agents scripts; do
  sync_path ".codex/$p" "$HOME/.codex/$p"
done
sync_path ".codex/skills/headroom-protocol" "$HOME/.codex/skills/headroom-protocol"
sync_path ".codex/skills/speak-human-tw"    "$HOME/.codex/skills/speak-human-tw"
sync_path ".codex/skills/experience-ledger"  "$HOME/.codex/skills/experience-ledger"
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
  for i in "${!SYNCED_SRC[@]}"; do
    diffout="$(rsync -an --links --force --delete --itemize-changes "${SYNCED_SRC[$i]}" "$(dirname "${SYNCED_DST[$i]}")/")"
    if [[ -n "$diffout" ]]; then
      log "ERROR: 同步後仍有差異: ${SYNCED_DST[$i]}"
      log "$diffout"
      FAIL=1
    fi
  done
  [[ $FAIL -eq 0 ]] || exit 1
  log "backup: $BACKUP"
  log "done. 全部同步路徑驗證一致；開新 session 驗證契約載入。"
else
  log "dry-run 完成；確認無誤後執行 scripts/sync.sh --apply"
fi
