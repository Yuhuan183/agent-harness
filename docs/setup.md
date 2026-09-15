# 配置說明 (開發者與 agent 適用)

把 agent-harness 的可攜契約套用到本機全域配置的完整流程. 設計原則:
**專案是唯一編修處, 全域是套用目標**; 機器狀態 (憑證, sessions, cache,
Codex `config.toml`, Claude Code `~/.claude.json` 的 MCP entry) 永不納入版控或同步.

## 目錄對應

`main/` 是唯一的全域部署來源. 根目錄保留給本專案專用的 `.claude/`,
`.agents/` 或其他配置; 除非明確加入 deployment manifest, 這些專案設定不會被
`scripts/sync.sh` 寫進 HOME.

| 專案內 | 全域目標 | 同步方式 |
| --- | --- | --- |
| `main/.agents/` (共用 skill 本體, `docs/`, 清單) | `~/.agents/` | script 自動; `skills/` 採 managed merge |
| `main/claude/` (契約檔, routing, 自有 skills, hooks, scripts, prompts, sh) | `~/.claude/` | script 自動 (tests/examples/plans 僅存 repo, 不部署) |
| `headroom mcp install --agent claude --proxy-url http://127.0.0.1:8787` | `~/.claude.json` | **手動執行** (機器狀態, 不入庫) |
| `main/claude/examples/headroom-mcp.legacy.json` | `~/.claude/mcp.json` | 僅供無 Claude CLI 的 legacy client 手動 merge |
| Antigravity CLI settings/MCP | `~/.gemini/` | 機器狀態, 不由本 repo 同步; 只有原生 `headroom wrap agy` 可用時才由 wrapper 管理 |

跨 agent runtime 知識 (`headroom-runtime.md`) 放 `main/.agents/docs/`, 不放進單一 agent 目錄.

### `main/` 是部署源, 不是工作環境

Claude Code 會從工作目錄底下任何巢狀 `.claude/skills/` 探索 skill, 並在叫用未限定名稱時
一併載入涵蓋當前檔案的限定名變體. 因此 `main/` 底下**不得出現會被探索到的設定路徑**:
skill 源檔放 `main/claude/skills/` (部署為 `~/.claude/skills/`), 契約源檔放
`CLAUDE.contract.md` (部署為 `~/.claude/CLAUDE.md`). 開發改 `main/`, 實際使用的一律是
`sync.sh` 部署後的 `$HOME` 版本. 此不變式由
`test_harness_sources_are_not_discoverable_while_developing` 守住.

共用 skill 原則上採 symlink 佈局: `main/claude/skills/<name>`
連到 `../../.agents/skills/<name>`. 需要平台專用
frontmatter 時使用薄 wrapper. 目前 Claude `task-observer` 以 wrapper 明確允許模型
自動啟動, `headroom-protocol` 也以同樣方式讓 agent 依資料大小與用途自行判斷.
兩者的內文與資源仍以 symlink 連回共用來源. `$HOME` 下三個目錄平級, 與專案同構, 因此
相對 symlink 原樣複製後仍成立 (與 lark 套件既有機制一致).
`main/.agents/skills/INSTALLED.txt` 只列本專案擁有的共用 skill. 部署時會精確同步這些
skill 與清單本身, 但保留 `~/.agents/skills/` 中其他第三方 skill; weekly integrity 也只對
清單內的管理範圍檢查 drift. 部署另會寫入 machine-local
`~/.agents/skills/.agent-harness-source`, 供維護工具把專案 skill 解析回
`main/.agents/skills/<name>`; 從 source checkout 執行維護工具時以該 checkout
優先, 避免舊部署標記導回過時分支. 不得把 HOME 部署副本當成編修來源.
`~/.agents` 並非公定標準 (AGENTS.md 標準管 repo 內檔案, Skills 標準管格式,
均未定義全域目錄), 採用它是因為本機工具鏈已以它為共用 skill 家目錄.

## 新機器 bootstrap (前置依賴)

sync 之前, 先確認以下工具鏈到位; plugin 與第三方 skill 一律視為本機自理,
不由本 repo 管理.

```bash
# 0. Python >= 3.11 (routing 工具鏈與測試使用 stdlib tomllib;
#    `python3-run` 會依序選擇 python3.13/3.12/3.11, 無須修改 shell profile)
brew install python@3.13

# 1. 基礎 CLI
brew install rtk ripgrep         # hook 依賴; 未裝時 fail-open, 可後補
                                 # 裝完不要跑 `rtk init`: hook 由本 repo settings.json 管理
                                 # 必須是 Headroom 以外的來源: `headroom wrap` 每次都會刪掉
                                 # ~/.headroom/bin/rtk 與指向它的 ~/.local/bin/rtk.
                                 # 用 `which -a rtk` 確認解析結果不在那兩個路徑
                                 # ripgrep 是 rtk 0.45+ 的 `rtk rg` 實際呼叫的程式, 缺了會讓
                                 # 每個 rg 命令以 `rtk: search failed` 收場
curl -LsSf https://astral.sh/uv/install.sh | sh   # headroom CLI 由 uv tool 管理
uv tool install headroom-ai      # 詳見 ~/.agents/docs/headroom-runtime.md
# Claude Code 與 Codex CLI 依官方文件安裝 (本 repo 不管理其版本)
```

- **Claude plugins** (figma, warp, ui-ux-pro-max…): 本 repo 不依賴任何 plugin. 要用的話
  自行安裝, 並把 enable 設定寫在 `~/.claude/settings.local.json`. `settings.json` 會以
  ownership-aware `merge-json` 更新 repo 擁有的 hook group, 其他 top-level key 與第三方
  group 會保留; 本機偏好仍建議放 `settings.local.json` (不入庫, 不同步).
- **第三方 skills (lark 全套等)**: 本機自帶, 非必要依賴, 不列入本專案的
  `INSTALLED.txt`, 也不由本 repo 部署; managed merge 會保留其既有目錄.
  `.skill-lock.json` 只是 installer 的 machine-local 版本快照, 不是專案 skill ownership 清單, 也不由本 repo 追蹤或部署.

## 套用步驟

```bash
cd ~/WorkSpace/agent-harness
scripts/sync.sh            # 1. dry-run: 檢視將發生的動作
scripts/sync.sh --apply    # 2. 實際套用
# 3. 安裝/更新 hclaude, hcodex, hagy 與 Auto Mode 快速指令
scripts/install-zsh-functions.sh
scripts/install-zsh-functions.sh --apply
# 4. 選用: 讓未經 wrap 的 Claude Code session 也能手動使用 Headroom MCP
headroom mcp install --agent claude --proxy-url http://127.0.0.1:8787
# 5. 開新 shell 與 agent session, 確認契約, skills 與 functions 載入
```

本專案採 **wrap-first, session-scoped** 的 Headroom 操作方式: Claude, Codex 分別使用
`hclaude`, `hcodex`; 原生 session 仍直接使用 `claude`, `codex`. 不要把
`ANTHROPIC_BASE_URL`, `OPENAI_BASE_URL` 或 Headroom provider 永久寫進 tracked config
或手寫進 shell profile; `headroom doctor` 看見 routed 只代表當下 machine-local CLI/shell
狀態, 不能據此判斷 Codex App.

這條通則有一個明文例外, 就是下面的 `headroom install apply --preset persistent-service`:
該 preset 會由 Headroom 自己在 `~/.zshrc` 維護一段 marker-fenced 區塊寫入這些變數. 選用
它是使用者的 machine-local 決定, 但要知道代價 — 上面「原生 session 直連」的分界就消失了,
`claude` 與 `hclaude` 一樣走 proxy, `/remote-control` 在所有 Claude session 都不可用,
而且 proxy 沒起來時每個 shell 的 agent 都連不出去. 想拿回 wrap-first 就
`headroom install remove`, 它會一併撤掉自己寫的區塊.

Claude Code 在自訂 `ANTHROPIC_BASE_URL` 之下會關閉 on-demand tool loading, 改成一次載入
全部 tool schema (upstream #746). `headroom wrap claude` 會設
`ENABLE_TOOL_SEARCH` 把它開回來, 預設 `true`, 也可用 `--tool-search auto`/`auto:N`/`false`
調整; 環境裡既有的值優先於預設, 會被原封不動保留. 走 `persistent-service` 常駐 routing 時,
這個變數必須跟 base URL 一起常駐, 否則原生 `claude` 會在沒有 deferral 的狀態下走 proxy.
完整語意與 `--1m` 的預設模型陷阱見 [`headroom-runtime.md`](../main/.agents/docs/headroom-runtime.md).

Antigravity CLI 的直接入口是 `agy`. `agy-auto` 已可用; `hagy`/`hagy-auto` 只有在
安裝版本真的提供 `headroom wrap agy` 時才會啟動, 否則 exit 127. 具日期的版本與
adapter 相容性查核集中在
[`headroom-runtime.md`](../main/.agents/docs/headroom-runtime.md); 不可用無效的 base URL
環境變數或靜默 fallback 冒充成功 routing.

Headroom 沒有 CLI context tools; Claude/Codex wrapper 不傳入那類選項. RTK 指引仍由
本專案契約管理, 不依賴 Headroom 注入或改寫 — 注入入口 `--serena-instructions` 預設關閉,
本 repo 不啟用. 升級 Headroom 後
若 `wrap` 的參數有變, 記得重跑 `scripts/install-zsh-functions.sh --apply`.
完整 lifecycle, Remote Control 與版本轉換說明見
[`headroom-runtime.md`](../main/.agents/docs/headroom-runtime.md).

### Agent 與 Headroom 快速指令

`scripts/install-zsh-functions.sh` 是唯一的 function 定義來源; 預設 dry-run, `--apply`
才修改個人的 `~/.zshrc`, 並且寫入前自動備份. installer 會移除早期文件曾提供, 內容
逐字相符的未標記舊版 block; 若內容曾被自行修改則保留, 不擅自刪除. 用
`--print-block` 可查看將安裝的完整定義.

| 平台 | 原生 | 原生 Auto | Headroom | Headroom Auto |
|---|---|---|---|---|
| Claude Code | `claude` | `claude-auto` | `hclaude` | `hclaude-auto` |
| Codex CLI | `codex` | `codex-auto` | `hcodex` | `hcodex-auto` |
| Antigravity CLI | `agy` | `agy-auto` | `hagy` | `hagy-auto` |

`claude-auto` 使用 Claude 原生 Auto Mode; `codex-auto` 預設只允許 workspace
寫入, 需要越界時才詢問; `agy-auto` 使用 `--mode accept-edits`. 各 `h*-auto` 保留相同安全邊界, 再經過
對應的 Headroom wrapper. `hagy*` 的 capability probe 失敗時必須停止, 不會改跑
未壓縮的 `agy`. 只有外層已有 Docker, VM 或 disposable sandbox 時, 才針對單次執行使用
`--dangerously-skip-permissions` 或 `--dangerously-bypass-approvals-and-sandbox`.
保留 bypass 警告, 不要在 Claude settings 設定
`"skipDangerousModePermissionPrompt": true`.

若使用者明確需要 always-on provider routing, 可另外使用
`headroom install apply --preset persistent-service`. 這是 machine-local 選用狀態,
不是 `sync.sh`, 快速指令, Codex CLI 或 Codex App 的預設. `persistent-service` 支援
`headroom install start`, `stop` 與 `restart`; 舊有 `persistent-task` profile 不支援
這些 lifecycle 指令. preset 轉換, 升級後 restart/re-apply 判斷與健康檢查見
[`headroom-runtime.md`](../main/.agents/docs/headroom-runtime.md).

`scripts/sync.sh` 的 dry-run 與 apply 都會先跑 JSON, shell, 兩側 routing, Claude pins 與
contract tests; 任何一項失敗都在寫入前停止. 所有可攜的 source→HOME 映射只定義在
`scripts/deployment-manifest.tsv`, `sync.sh` 與 weekly integrity 共讀這一份; 新增或改名部署
成品時不得另建第二份清單.

**兩個檔案是合併部署, 不是覆蓋**, 因為它們同時有別的寫入者:

- **`settings.json`** (`merge-json`, manifest 第三欄). 三個寫入者: 本 repo, Claude Code 自己
  (`/model`, `/effort`), 與第三方 hook 安裝程式. 合併看「所有權」而不是位置 —— 命令含
  `$HOME/.claude/hooks/` 或 `rtk hook claude` 的 hook group 屬於本 repo, 整組替換 (所以過期
  指令是被更新, 不會變成重複兩份); 其餘 group, repo 未定義的事件與 top-level key 一律原樣
  保留, `permissions.allow` 取聯集. 每次執行都會列出保留了哪些項目, 因此不需要覆寫逃生口,
  `--accept-settings-overwrite` 已移除.

兩者的部署後校驗都不是 byte 相等, 而是「重跑一次 merge 不再改變任何東西」, `sync.sh` 與
weekly integrity 都會驗.

另外兩件會讓 apply 停下或被判成 drift 的事:

- 既有的 `~/.claude/CLAUDE.md` 內容從未出現在本 repo 歷史 (是別人的
  指引, 不是舊版契約) 時, apply 停止. 先手動合併, 或明確用 `--accept-contract-takeover` 接管.
- 切換 Claude preset 要在 source checkout 執行
  `main/claude/scripts/model-routing activate-profile --profile <balanced|fast|quality_guarded>`,
  確認 git diff, 再 sync 並開新 session. 只改 `~/.claude` 會被 weekly integrity 視為相對
  Git source 的 drift.

## 專案層: 給另一個 repo 一份事實包

全域部署管的是**你**: 角色, 派工, 驗證, 閘, 全部住在 HOME. 專案層管的是**某個 repo**: 它怎麼跑測試, 真相源在哪, 有什麼陷阱. 路線與階段在[專案層計畫](../main/project/README.md#已定的決定) (2026-09-11 結案); 這裡只講怎麼用.

**誰該裝**: 還沒有任何契約檔的 repo. **誰不該裝**: 已經有成熟 `CLAUDE.md` 或 `AGENTS.md` 的 repo —— 七格事實它們自己寫過了, 裝進去只是重複 (工作區 15 個 repo 裡有 5 個是這種). **已量到**: 區塊會自己抵達 session, 不用 session 去讀 (10/10, 零工具呼叫). **沒量到**: 它會不會因此改變行為 —— 唯一一格兩臂都滿分, 所以這裡不主張行為效應.

```bash
main/.agents/scripts/python3-run scripts/project-init.py <repo>            # dry-run: 會寫什麼, 附 diff
main/.agents/scripts/python3-run scripts/project-init.py <repo> --apply    # 第一次寫事實骨架後停下; 填完再跑一次才渲染
main/.agents/scripts/python3-run scripts/project-init.py <repo> --verify   # 0 一致, 1 區塊被改過, 4 沒裝
```

事實只住一處, `<repo>/.agent-harness/facts.toml`; 兩個契約區塊 (repo 根目錄的 `CLAUDE.md` 與 `AGENTS.md`) 從它渲染, 以標記圍欄合併進去, 團隊原有的內容一字不動. 沒填完的事實不渲染 —— 填不出來的那一格就是這個 repo 還沒回答的問題. 不裝 hook, 不裝 git hook, 不對本 repo 或 HOME 執行 (會拒絕).

## 驗收

- 新 session 中全域 CLAUDE.md 只有兩節短規則; `provider-routing`, `baton-dispatch`,
  `headroom-protocol` 出現在可用 skill 清單且能按需載入.
- `headroom-protocol` 與 `task-observer` 是平台 wrapper, 其共用內文與資源分別連回
  `~/.agents/skills/<name>`.
- 跑 2–3 個真實任務比對遵循度與 token (方法見 `contract-slimming.md` 的驗收段).
- 「client 真的在讀這個目標」的觀察記在 `scripts/deployment-verification.tsv`: manifest 每個目標一列,
  帶觀察日, client 版本與觀察到什麼 (skill 出現在 session 的清單, hook 回 exit 2, resolver 讀到
  routing 檔). 這和 weekly integrity 的 parity 不同: 位元組一致不代表 client 還在讀那個路徑.
  超過 90 天測試會紅, 處置是重新觀察並更新該列, 不是調高天數.

## 回滾

不做備份. 每一個部署出去的位元組都在 git 裡, 所以回滾就是把 repo 切回想要的
版本再重跑一次部署:

```bash
git checkout <ref> -- main/   # 或整個 checkout 到某個 commit
scripts/sync.sh               # dry-run 確認影響面
scripts/sync.sh --apply
```

機器狀態不需要回滾 — `settings.json` 走 merge, 本來就不會被整份
覆蓋; `~/.claude/CLAUDE.md` 若內容不曾出現在本 repo 歷史,
apply 會直接停下而不是覆蓋. 唯一沒有還原路徑的是「手動改在 repo 全權擁有的目錄裡」
的檔案 (例如自己往 `~/.claude/hooks/` 塞東西), 那些會被 `rsync --delete` 清掉 —
這類本機偏好請放 `settings.local.json`.

## 修改流程 (日常)

1. 在專案內編修 → `git diff` review.
2. `scripts/sync.sh` dry-run 確認影響面 → `--apply`.
3. 新 session 驗證後 commit.
