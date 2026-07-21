# 配置說明（開發者 / 智能體適用）

把 agent-harness 的可攜契約套用到本機全域配置的完整流程。設計原則：
**專案是唯一編修處，全域是套用目標**；機器狀態（憑證、sessions、cache、
codex `config.toml`、claude `mcp_servers.json` 的本機路徑段）永不納入版控或同步。

## 目錄對應

| 專案內 | 全域目標 | 同步方式 |
| --- | --- | --- |
| `.agents/`（共用 skill 本體、`docs/`、清單） | `~/.agents/` | script 自動 |
| `.claude/`（契約檔 + 自有 skills + hooks/scripts/tests） | `~/.claude/` | script 自動 |
| `.claude/examples/headroom-mcp.merge.json` | `~/.claude/mcp_servers.json` | **手動 merge**（機器狀態，不入庫） |
| `.codex/AGENTS.md`、`README.md`、`prompts/`、`agents/`、skill symlink | `~/.codex/` | script 自動 |
| `.codex/config.merge.toml` | `~/.codex/config.toml` | **手動 merge**（見 `.codex/DEPLOY.md`） |

跨 agent runtime 知識（`headroom-runtime.md`）在 `.agents/docs/`，Claude 與 Codex 共用同一份，
不在單一 agent 目錄下各留一份。舊機器若殘留 `~/.claude/docs/`（重整前的位置），可於套用後
手動清除——方法論已移至專案 `docs/`、runtime 知識已移至 `~/.agents/docs/`。

共用 skill 採 symlink 佈局：`.claude/skills/<name>` 與 `.codex/skills/<name>` 都是
`../../.agents/skills/<name>` 的相對連結。`$HOME` 下三個目錄平級、與專案同構，
因此 symlink 原樣複製後在全域一樣成立（與 lark 套件既有機制一致）。
`~/.agents` 並非公定標準（AGENTS.md 標準管 repo 內檔案、Skills 標準管格式，
均未定義全域目錄），採用它是因為本機工具鏈已以它為共用 skill 家目錄。

## 新機器 bootstrap（前置依賴）

sync 之前，先確認以下工具鏈到位；除 codex plugin 外，其他 plugin／第三方 skill
一律視為本機自理，不由本 repo 管理。

```bash
# 1. 基礎 CLI
brew install rtk                 # hook 依賴；未裝時 fail-open，可后補
curl -LsSf https://astral.sh/uv/install.sh | sh   # headroom CLI 由 uv tool 管理
uv tool install headroom-ai      # 詳見 ~/.agents/docs/headroom-runtime.md
# Claude Code 與 Codex CLI 依官方文件安裝（本 repo 不管理其版本）

# 2. 唯一強依賴的 Claude plugin：codex（marketplace 已由 settings.json 帶入）
claude plugin install codex@openai-codex
```

- **其他 Claude plugins**（figma、warp、ui-ux-pro-max…）：非本 repo 依賴。要用的話
  自行安裝，並把 enable 設定寫在 `~/.claude/settings.local.json`——`settings.json`
  會被 sync 整份覆蓋，本機偏好一律放 `settings.local.json`（不入庫、不同步）。
- **第三方 skills（lark 全套等）**：本機自帶、非必要依賴，本 repo 只以
  `.agents/skills/INSTALLED.txt` 與 `.skill-lock.json` 記錄現況供比對，不提供重裝流程；
  缺少時不影響本 repo 的契約與部署。

## 套用步驟

```bash
cd ~/WorkSpace/agent-harness
scripts/sync.sh            # 1. dry-run：檢視將發生的動作
scripts/sync.sh --apply    # 2. 實際套用（自動備份到 backups/<timestamp>/）
# 3a. claude MCP：把 .claude/examples/headroom-mcp.merge.json 手動併入 ~/.claude/mcp_servers.json
# 3b. codex 本機設定：把 .codex/config.merge.toml 手動併入 ~/.codex/config.toml
# 4. 開新 Claude Code / Codex session，確認契約與 skills 載入
```

## 驗收

- 新 session 中全域 CLAUDE.md 僅約 600 tokens；`provider-routing`、`baton-dispatch`、
  `headroom-protocol` 出現在可用 skill 清單且能按需載入。
- `ls -la ~/.claude/skills/headroom-protocol ~/.codex/skills/headroom-protocol`
  均為指向 `~/.agents/skills/headroom-protocol` 的 symlink。
- 跑 2–3 個真實任務比對遵循度與 token（方法見 `global-claude-md-slimming.md`）。

## 回滾

`scripts/sync.sh --apply` 每次執行前會把被覆蓋的目標完整備份到
`backups/<timestamp>/`（gitignored）；把備份內容複製回原位即可回滾。

## 修改流程（日常）

1. 在專案內編修 → `git diff` review。
2. `scripts/sync.sh` dry-run 確認影響面 → `--apply`。
3. 新 session 驗證後 commit。
