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
| `main/claude/`（契約檔、routing、自有 skills、hooks、scripts、prompts、sh） | `~/.claude/` | script 自動（tests/examples/plans 僅存 repo，不部署） |
| `headroom mcp install --agent claude --proxy-url http://127.0.0.1:8787` | `~/.claude.json` | **手動執行**（機器狀態，不入庫） |
| `main/claude/examples/headroom-mcp.legacy.json` | `~/.claude/mcp.json` | 僅供無 Claude CLI 的 legacy client 手動 merge |
| `main/codex/AGENTS.contract.md`（部署為 `AGENTS.md`）、`README.md`、`ANALYSIS.md`、`DEPLOY.md`、`model-routing.toml`、`prompts/`、`agents/`、`scripts/`、skills（含 `leaf-dispatch` 與 symlink） | `~/.codex/` | script 自動 |
| `main/codex/config.merge.toml` | `~/.codex/config.toml` | script 自動 **section-scoped merge**（只寫 `[agents]`／`[agents.*]`，見 `main/codex/DEPLOY.md`） |
| Antigravity CLI settings／MCP | `~/.gemini/` | 機器狀態，不由本 repo 同步；只有原生 `headroom wrap agy` 可用時才由 wrapper 管理 |

跨 agent runtime 知識（`headroom-runtime.md`）在 `main/.agents/docs/`，Claude 與 Codex 共用同一份，
不在單一 agent 目錄下各留一份。舊機器若殘留 `~/.claude/docs/`（重整前的位置），可於套用後
手動清除——方法論已移至專案 `docs/`、runtime 知識已移至 `~/.agents/docs/`。

### `main/` 是部署源，不是工作環境

Claude Code 會從工作目錄底下任何巢狀 `.claude/skills/` 探索 skill,並在叫用未限定名稱時
一併載入涵蓋當前檔案的限定名變體。因此 `main/` 底下**不得出現會被探索到的設定路徑**:
skill 源檔放 `main/claude/skills/`(部署為 `~/.claude/skills/`),契約源檔放
`CLAUDE.contract.md`(部署為 `~/.claude/CLAUDE.md`)。開發改 `main/`,實際使用的一律是
`sync.sh` 部署後的 `$HOME` 版本。此不變式由
`test_harness_sources_are_not_discoverable_while_developing` 守住。

共用 skill 原則上採 symlink 佈局：`main/claude/skills/<name>` 與
`main/codex/skills/<name>` 都連到 `../../.agents/skills/<name>`。需要平台專用
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
  `settings.json` 會以 ownership-aware `merge-json` 更新 repo 擁有的 hook group，其他 top-level key 與第三方 group 會保留；本機偏好仍建議放 `settings.local.json`（不入庫、不同步）。
- **第三方 skills（lark 全套等）**：本機自帶、非必要依賴，不列入本專案的
  `INSTALLED.txt`，也不由本 repo 部署；managed merge 會保留其既有目錄。
  `.skill-lock.json` 只是 installer 的 machine-local 版本快照，不是專案 skill ownership 清單，也不由本 repo 追蹤或部署。

## 套用步驟

```bash
cd ~/WorkSpace/agent-harness
scripts/sync.sh            # 1. dry-run：檢視將發生的動作
scripts/sync.sh --apply    # 2. 實際套用
# 3. 安裝／更新 hclaude、hcodex、hagy 與 Auto Mode 快速指令
scripts/install-zsh-functions.sh
scripts/install-zsh-functions.sh --apply
# 4. 選用：讓未經 wrap 的 Claude Code session 也能手動使用 Headroom MCP
headroom mcp install --agent claude --proxy-url http://127.0.0.1:8787
# 5. 開新 shell 與 agent session，確認契約、skills 與 functions 載入
```

本專案採 **wrap-first、session-scoped** 的 Headroom 操作方式：Claude、Codex 分別使用
`hclaude`、`hcodex`；原生 session 仍直接使用 `claude`、`codex`。不要把
`ANTHROPIC_BASE_URL`、`OPENAI_BASE_URL` 或 Headroom provider 永久寫進 tracked config
或 shell profile；`headroom doctor` 看見 routed 只代表當下 machine-local CLI／shell
狀態，不能據此判斷 Codex App。

Antigravity CLI 的直接入口是 `agy`。`agy-auto` 已可用；`hagy`／`hagy-auto` 只有在
安裝版本真的提供 `headroom wrap agy` 時才會啟動，否則 exit 127。具日期的版本與
adapter 相容性查核集中在
[`headroom-runtime.md`](../main/.agents/docs/headroom-runtime.md)；不可用無效的 base URL
環境變數或靜默 fallback 冒充成功 routing。

Claude／Codex 的 `--no-context-tool` 由本專案管理 RTK 指引，避免 wrapper 重寫契約。
Antigravity 上游 adapter 尚未提供同名選項，不傳未知參數。
完整 lifecycle、Remote Control 與版本轉換說明見
[`headroom-runtime.md`](../main/.agents/docs/headroom-runtime.md)。

### Agent 與 Headroom 快速指令

`scripts/install-zsh-functions.sh` 是唯一的 function 定義來源；預設 dry-run，`--apply`
才修改個人的 `~/.zshrc`，並且寫入前自動備份。installer 會移除早期文件曾提供、內容
逐字相符的未標記舊版 block；若內容曾被自行修改則保留，不擅自刪除。用
`--print-block` 可查看將安裝的完整定義。

| 平台 | 原生 | 原生 Auto | Headroom | Headroom Auto |
|---|---|---|---|---|
| Claude Code | `claude` | `claude-auto` | `hclaude` | `hclaude-auto` |
| Codex CLI | `codex` | `codex-auto` | `hcodex` | `hcodex-auto` |
| Antigravity CLI | `agy` | `agy-auto` | `hagy` | `hagy-auto` |

`claude-auto` 使用 Claude 原生 Auto Mode；`codex-auto` 預設只允許 workspace
寫入，需要越界時才詢問；`agy-auto` 使用 `--mode accept-edits`。各 `h*-auto` 保留相同安全邊界，再經過
對應的 Headroom wrapper。`hagy*` 的 capability probe 失敗時必須停止，不會改跑
未壓縮的 `agy`。只有外層已有 Docker、VM 或 disposable sandbox 時，才針對單次執行使用
`--dangerously-skip-permissions` 或 `--dangerously-bypass-approvals-and-sandbox`。
保留 bypass 警告，不要在 Claude settings 設定
`"skipDangerousModePermissionPrompt": true`。

若使用者明確需要 always-on provider routing，可另外使用
`headroom install apply --preset persistent-service`。這是 machine-local 選用狀態，
不是 `sync.sh`、快速指令、Codex CLI 或 Codex App 的預設。`persistent-service` 支援
`headroom install start`、`stop` 與 `restart`；舊有 `persistent-task` profile 不支援
這些 lifecycle 指令。preset 轉換、升級後 restart／re-apply 判斷與健康檢查見
[`headroom-runtime.md`](../main/.agents/docs/headroom-runtime.md)。

`scripts/sync.sh` 的 dry-run 與 apply 都會先跑 JSON／shell／兩側 routing／Claude pins／contract tests；任何失敗都在寫入前停止。
所有可攜 source→HOME 映射只定義於 `scripts/deployment-manifest.tsv`；`sync.sh` 與 weekly integrity
共同讀取它，新增或改名部署成品時不得另建第二份清單。
全域 `settings.json` 以 `merge-json` 模式部署（manifest 第三欄），因為這個檔案有三個寫入者：本 repo、
Claude Code 自己（`/model`、`/effort`）與第三方 hook 安裝程式。合併以「所有權」而非位置判斷：命令含
`$HOME/.claude/hooks/` 或 `rtk hook claude` 的 hook group 屬本 repo，整組替換（過期指令會被更新而不是
變成重複兩份）；其餘 group、repo 未定義的事件與 top-level key 一律原樣保留，`permissions.allow` 取聯集。
每次執行都會列出保留了哪些項目。因此不需要覆寫逃生口，`--accept-settings-overwrite` 已移除。
`~/.codex/config.toml` 同理，以 `merge-toml` 模式部署：只寫入 `[agents]` 與 `[agents.*]`，其餘 section、註解與格式逐字保留；repo 未宣告的 `[agents.*]`（使用者自建 agent）保留並回報。兩者的部署後校驗都不是 byte 相等，而是「重跑 merge 不再改變任何東西」，`sync.sh` 與 weekly integrity 都會驗。若既有的 `~/.claude/CLAUDE.md` 或 `~/.codex/AGENTS.md`
內容從未出現在本 repo 歷史（別人的指引，不是舊版契約），apply 也會停止：先手動合併，或明確用
`--accept-contract-takeover` 接管。切換 Claude preset 時，先在 source checkout 執行
`main/claude/scripts/model-routing activate-profile --profile <balanced|fast|quality_guarded>`，確認 git diff，
再 sync 並開新 session；只改 `~/.claude` 會被 weekly integrity 視為相對 Git source 的 drift。

## 驗收

- 新 session 中全域 CLAUDE.md 僅約 600 tokens；`provider-routing`、`baton-dispatch`、
  `headroom-protocol` 出現在可用 skill 清單且能按需載入。
- `~/.codex/skills/headroom-protocol` 是指向共用來源的 symlink；Claude 的
  `headroom-protocol` 與 `task-observer` 是平台 wrapper，其共用內文與資源分別連回
  `~/.agents/skills/<name>`。
- 跑 2–3 個真實任務比對遵循度與 token（方法見 `contract-slimming.md` 的驗收段）。

## 回滾

不做備份。每一個部署出去的位元組都在 git 裡，所以回滾就是把 repo 切回想要的
版本再重跑一次部署：

```bash
git checkout <ref> -- main/   # 或整個 checkout 到某個 commit
scripts/sync.sh               # dry-run 確認影響面
scripts/sync.sh --apply
```

機器狀態不需要回滾——`settings.json` 與 `config.toml` 走 merge，本來就不會被整份
覆蓋；`~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md` 若內容不曾出現在本 repo 歷史，
apply 會直接停下而不是覆蓋。唯一沒有還原路徑的是「手動改在 repo 全權擁有的目錄裡」
的檔案（例如自己往 `~/.claude/hooks/` 塞東西），那些會被 `rsync --delete` 清掉——
這類本機偏好請放 `settings.local.json`。

## 修改流程（日常）

1. 在專案內編修 → `git diff` review。
2. `scripts/sync.sh` dry-run 確認影響面 → `--apply`。
3. 新 session 驗證後 commit。
