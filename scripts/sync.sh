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
sync_path() { # $1 = repo 相對來源  $2 = 全域目標
  local src="$REPO/$1" dst="$2"
  [[ -e "$src" ]] || { log "skip (missing in repo): $1"; return; }
  if [[ -e "$dst" && $APPLY -eq 1 ]]; then
    mkdir -p "$BACKUP/$(dirname "$1")"
    cp -R "$dst" "$BACKUP/$1"
  fi
  run mkdir -p "$(dirname "$dst")"
  # --force：允許以 symlink 取代既有實體目錄（如 ~/.codex/skills/headroom-protocol）
  run rsync -a --links --force "$src" "$(dirname "$dst")/"
}

log "== agent-harness sync (apply=$APPLY) =="

# --- .agents：共用 skill 本體與跨 agent 知識先到位（symlink 目標） ---
sync_path ".agents/skills/headroom-protocol" "$HOME/.agents/skills/headroom-protocol"
sync_path ".agents/.skill-lock.json"         "$HOME/.agents/.skill-lock.json"
sync_path ".agents/docs"                      "$HOME/.agents/docs"
sync_path ".agents/README.md"                 "$HOME/.agents/README.md"

# --- .claude：可攜契約（mcp_servers.json 為機器狀態，僅提示手動 merge） ---
for p in CLAUDE.md README.md RTK.md settings.json \
         agents hooks prompts scripts sh tests examples; do
  sync_path ".claude/$p" "$HOME/.claude/$p"
done
log "note: .claude/mcp_servers.json 為機器狀態（含本機路徑），不自動覆蓋；新增 headroom MCP 時手動 merge .claude/examples/headroom-mcp.merge.json。"
sync_path ".claude/plans/orchestration-plan.md" "$HOME/.claude/plans/orchestration-plan.md"
# 自有 skills（逐個列，避免動到全域其他已安裝 skill 與 lark symlinks）
for s in baton-dispatch provider-routing headroom-protocol; do
  sync_path ".claude/skills/$s" "$HOME/.claude/skills/$s"
done

# --- .codex：可攜契約（config.toml 為機器狀態，僅提示手動 merge） ---
for p in AGENTS.md README.md ANALYSIS.md DEPLOY.md prompts agents; do
  sync_path ".codex/$p" "$HOME/.codex/$p"
done
sync_path ".codex/skills/headroom-protocol" "$HOME/.codex/skills/headroom-protocol"
log "note: .codex/config.merge.toml 需手動 merge 進 ~/.codex/config.toml（見 DEPLOY.md），不自動覆蓋。"

# --- 驗證 ---
if [[ $APPLY -eq 1 ]]; then
  for l in "$HOME/.claude/skills/headroom-protocol" "$HOME/.codex/skills/headroom-protocol"; do
    [[ -f "$l/SKILL.md" ]] || { log "ERROR: $l 未能解析到 SKILL.md"; exit 1; }
  done
  log "backup: $BACKUP"
  log "done. 開新 session 驗證契約載入。"
else
  log "dry-run 完成；確認無誤後執行 scripts/sync.sh --apply"
fi
