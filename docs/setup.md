# 配置說明（開發者 / 智能體適用）

把 agent-harness 的可攜契約套用到本機全域配置的完整流程。設計原則：
**專案是唯一編修處，全域是套用目標**；機器狀態（憑證、sessions、cache、
Codex `config.toml`、Claude Code `~/.claude.json` 的 MCP entry）永不納入版控或同步。

## 目錄對應

`main/` 是唯一的全域部署來源。根目錄保留給本專案專用的 `.claude/`、`.codex/`、
`.agents/` 或其他配置；除非明確加入 deployment manifest，這些專案設定不會被
`scripts/sync.sh` 寫進 HOME。

| 專案內 | 全域目標 | 同步方式 |
| --- | --- | --- |
| `main/.agents/`（共用 skill 本體、`docs/`、清單） | `~/.agents/` | script 自動；`skills/` 採 managed merge |
| `main/.claude/`（契約檔、routing、自有 skills、hooks、scripts、prompts、sh） | `~/.claude/` | script 自動（tests/examples/plans 僅存 repo，不部署） |
| `headroom mcp install --agent claude --proxy-url http://127.0.0.1:8787` | `~/.claude.json` | **手動執行**（機器狀態，不入庫） |
| `main/.claude/examples/headroom-mcp.legacy.json` | `~/.claude/mcp.json` | 僅供無 Claude CLI 的 legacy client 手動 merge |
| `main/.codex/AGENTS.contract.md`（部署為 `AGENTS.md`）、`README.md`、`ANALYSIS.md`、`DEPLOY.md`、`model-routing.toml`、`prompts/`、`agents/`、`scripts/`、skills（含 `leaf-dispatch` 與 symlink） | `~/.codex/` | script 自動 |
| `main/.codex/config.merge.toml` | `~/.codex/config.toml` | **手動 merge**（見 `main/.codex/DEPLOY.md`） |

跨 agent runtime 知識（`headroom-runtime.md`）在 `main/.agents/docs/`，Claude 與 Codex 共用同一份，
不在單一 agent 目錄下各留一份。舊機器若殘留 `~/.claude/docs/`（重整前的位置），可於套用後
手動清除——方法論已移至專案 `docs/`、runtime 知識已移至 `~/.agents/docs/`。

共用 skill 原則上採 symlink 佈局：`main/.claude/skills/<name>` 與
`main/.codex/skills/<name>` 都連到 `../../.agents/skills/<name>`。需要平台專用
frontmatter 時使用薄 wrapper；目前 Claude `task-observer` 以 wrapper 明確允許模型
自動啟動，`headroom-protocol` 也以同樣方式讓 agent 依資料大小與用途自行判斷；
內文與資源仍以 symlink 連回共用來源。`$HOME` 下三個目錄平級、與專案同構，因此
相對 symlink 原樣複製後仍成立（與 lark 套件既有機制一致）。
`main/.agents/skills/INSTALLED.txt` 只列本專案擁有的共用 skill。部署時會精確同步這些
skill 與清單本身，但保留 `~/.agents/skills/` 中其他第三方 skill；weekly integrity 也只對
清單內的管理範圍檢查 drift。部署另會寫入 machine-local
`~/.agents/skills/.agent-harness-source`，供維護工具把專案 skill 解析回
`main/.agents/skills/<name>`；從 source checkout 執行維護工具時以該 checkout
優先，避免舊部署標記導回過時分支。不得把 HOME 部署副本當成編修來源。
`~/.agents` 並非公定標準（AGENTS.md 標準管 repo 內檔案、Skills 標準管格式，
均未定義全域目錄），採用它是因為本機工具鏈已以它為共用 skill 家目錄。

## 新機器 bootstrap（前置依賴）

sync 之前，先確認以下工具鏈到位；除 codex plugin 外，其他 plugin／第三方 skill
一律視為本機自理，不由本 repo 管理。

```bash
# 0. Python >= 3.11（routing 工具鏈與測試使用 stdlib tomllib；
#    `python3-run` 會依序選擇 python3.13／3.12／3.11，無須修改 shell profile）
brew install python@3.13

# 1. 基礎 CLI
brew install rtk                 # hook 依賴；未裝時 fail-open，可後補
curl -LsSf https://astral.sh/uv/install.sh | sh   # headroom CLI 由 uv tool 管理
uv tool install headroom-ai      # 詳見 ~/.agents/docs/headroom-runtime.md
# Claude Code 與 Codex CLI 依官方文件安裝（本 repo 不管理其版本）

# 2. 唯一強依賴的 Claude plugin：codex（marketplace 已由 settings.json 帶入）
claude plugin install codex@openai-codex
```

- **其他 Claude plugins**（figma、warp、ui-ux-pro-max…）：非本 repo 依賴。要用的話
  自行安裝，並把 enable 設定寫在 `~/.claude/settings.local.json`——`settings.json`
  會被 sync 整份覆蓋，本機偏好一律放 `settings.local.json`（不入庫、不同步）。
- **第三方 skills（lark 全套等）**：本機自帶、非必要依賴，不列入本專案的
  `INSTALLED.txt`，也不由本 repo 部署；managed merge 會保留其既有目錄。
  `.skill-lock.json` 只是 installer 版本快照，不是專案 skill ownership 清單。

## 套用步驟

```bash
cd ~/WorkSpace/agent-harness
scripts/sync.sh            # 1. dry-run：檢視將發生的動作
scripts/sync.sh --apply    # 2. 實際套用（自動備份到 backups/<timestamp>/）
# 3a. Codex always-on proxy（machine-local，不由 sync 管理）
rtk headroom install apply --profile default --preset persistent-service \
  --runtime python --scope provider --providers manual --target codex \
  --port 8787 --backend anthropic --no-telemetry
# 3b. Claude Code MCP（installer 會解析 headroom 的 machine-local 絕對路徑）
headroom mcp install --agent claude --proxy-url http://127.0.0.1:8787
# 3c. codex 本機設定：把 main/.codex/config.merge.toml 手動併入 ~/.codex/config.toml
# 4. 開新 Claude Code / Codex session，確認契約與 skills 載入
```

Claude Code 平常直接執行 `claude`，需要 Headroom proxy 時才執行
`headroom wrap claude --no-context-tool`。不要把 `ANTHROPIC_BASE_URL` 永久寫進 shell
profile；RTK 指引由本專案契約管理，`--no-context-tool` 可避免 wrapper 重寫契約。
完整 lifecycle、Remote Control 與版本轉換說明見
[`headroom-runtime.md`](../main/.agents/docs/headroom-runtime.md)。

### 選用的 Auto Mode shell functions

需要減少互動確認時，可把以下 functions 放進個人的 `~/.zshrc`。一般 Auto Mode
保留 sandbox；不要把完全繞過安全機制的 `--dangerously-*` 設為 `claude` 或 `codex`
的預設 alias。

```bash
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
```

可手動貼進 `~/.zshrc`，或執行 `scripts/install-zsh-functions.sh`（dry-run 預設，
`--apply` 才寫入；冪等、寫入前自動備份）套用同一份區塊。

`claude-auto` 使用 Claude 原生 Auto Mode；`codex-auto` 不詢問但只允許 workspace
寫入。`hclaude-auto`、`hcodex-auto` 行為相同，另外經過 Headroom。只有外層已有
Docker、VM 或 disposable sandbox 時，才針對單次執行使用
`--dangerously-skip-permissions` 或 `--dangerously-bypass-approvals-and-sandbox`。
保留 bypass 警告，不要在 Claude settings 設定
`"skipDangerousModePermissionPrompt": true`。

dry-run 與 apply 都會先跑 JSON／shell／兩側 routing／Claude pins／contract tests；任何失敗都在寫入前停止。
所有可攜 source→HOME 映射只定義於 `scripts/deployment-manifest.tsv`；`sync.sh` 與 weekly integrity
共同讀取它，新增或改名部署成品時不得另建第二份清單。
全域 `settings.json` 以 `merge-json` 模式部署（manifest 第三欄），因為這個檔案有三個寫入者：本 repo、
Claude Code 自己（`/model`、`/effort`）與第三方 hook 安裝程式。合併以「所有權」而非位置判斷：命令含
`$HOME/.claude/hooks/` 或 `rtk hook claude` 的 hook group 屬本 repo，整組替換（過期指令會被更新而不是
變成重複兩份）；其餘 group、repo 未定義的事件與 top-level key 一律原樣保留，`permissions.allow` 取聯集。
每次執行都會列出保留了哪些項目。因此不需要覆寫逃生口，`--accept-settings-overwrite` 已移除。若既有的 `~/.claude/CLAUDE.md` 或 `~/.codex/AGENTS.md`
內容從未出現在本 repo 歷史（別人的指引，不是舊版契約），apply 也會停止：先手動合併，或明確用
`--accept-contract-takeover` 接管。切換 Claude preset 時，先在 source checkout 執行
`main/.claude/scripts/model-routing activate-profile --profile <balanced|fast|quality_guarded>`，確認 git diff，
再 sync 並開新 session；只改 `~/.claude` 會被 weekly integrity 視為相對 Git source 的 drift。

## 驗收

- 新 session 中全域 CLAUDE.md 僅約 600 tokens；`provider-routing`、`baton-dispatch`、
  `headroom-protocol` 出現在可用 skill 清單且能按需載入。
- `~/.codex/skills/headroom-protocol` 是指向共用來源的 symlink；Claude 的
  `headroom-protocol` 與 `task-observer` 是平台 wrapper，其共用內文與資源分別連回
  `~/.agents/skills/<name>`。
- 跑 2–3 個真實任務比對遵循度與 token（方法見 `contract-slimming.md` 的驗收段）。

## 回滾

`scripts/sync.sh --apply` 每次執行前會把被覆蓋的目標完整備份到
`backups/<timestamp>/`（gitignored）；把備份內容複製回原位即可回滾。

## 修改流程（日常）

1. 在專案內編修 → `git diff` review。
2. `scripts/sync.sh` dry-run 確認影響面 → `--apply`。
3. 新 session 驗證後 commit。
