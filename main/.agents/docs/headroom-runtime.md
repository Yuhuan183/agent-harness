# Headroom Runtime Guide

> 2026-08-10 本機查核: CLI 與 persistent-service proxy 都是 `headroom-ai 0.34.0`
> (`headroom install status` running/healthy, `doctor` 的 version check pass).
> 已退場的 context-tool 舊旗標實測被 `wrap claude` 拒絕 (exit 1), 不帶它則 exit 0;
> `wrap agy` 仍不存在. 這只證明本機安裝版本與 live service capability, 不等於上游
> latest release 證據.

> 只記錄跨機器的架構, 操作邊界與版本轉換. venv, PID, port 與 profile 名稱屬 machine-local state, 不進 git.

## 專案採用方式

本專案採 **wrap-first, session-scoped**: 快速指令明確建立 Headroom session; 原生
agent 指令維持直連或使用者自己的 machine-local 狀態.

| Surface | 標準入口 | 行為 |
|---|---|---|
| Claude Code 原生 session | `claude` | 直連 Anthropic, 保留 Remote Control |
| Claude Code Headroom session | `headroom wrap claude` | 只在這個 session 注入 `ANTHROPIC_BASE_URL`; Remote Control 不可用; 預設另註冊 Serena code-memory MCP |
| Codex 原生 session | `codex` | 使用當下 machine-local 設定; 本 repo 不建立永久 Headroom provider |
| Codex Headroom session | `headroom wrap codex` | 由 wrapper 建立該次 session 所需的 proxy 與 provider routing; 預設另註冊 Serena code-memory MCP |
| Antigravity CLI 原生 session | `agy` | 直連 Google Cloud Code Assist |
| Antigravity CLI Headroom session | `headroom wrap agy` | 需要 Headroom 原生 `agy` adapter; 未支援時 `hagy` 必須 fail closed, 不得靜默直連 |
| Headroom MCP | `headroom mcp install --agent <agent> --proxy-url http://127.0.0.1:8787` | 提供 marker retrieve, compress 與 stats; 實際可用 agent 以安裝版本的 registrar 為準 |

不得把 `ANTHROPIC_BASE_URL`, `OPENAI_BASE_URL` 或其他 provider endpoint 永久寫入
git-tracked agent settings, 也不得手寫進 shell profile. 唯一的例外是使用者明確選擇
`headroom install apply --preset persistent-service`: 該 preset 由 Headroom 自己在
`~/.zshrc` 維護一個 marker-fenced 區塊寫入這些變數, 屬 machine-local 選用狀態, 不是本
repo 的預設. 選了它就等於放棄 wrap-first 的分界 — 上表「原生 session」那幾列不再成立,
`claude` 與 `hclaude` 同樣走 proxy, Remote Control 在**所有** Claude session 都不可用.
RTK 指引由 harness 契約管理. Headroom
v0.34 起已移除 CLI context tools, 因此 Claude 與 Codex wrap 不再傳入舊版選項; 舊旗標
會被 CLI 明確拒絕並附遷移訊息, 不是被忽略.

v0.34 把注入入口換成兩個新的預設值, 兩者都要知道:

- `--serena-instructions` 預設關閉, 本 repo 不啟用. 它會把 marker-fenced 區塊寫進
  **當前工作目錄**的 `CLAUDE.md` 或 `AGENTS.md`; 在本 repo 根目錄執行等於憑空生出一份
  會被 Claude Code 載入的專案指引, 繞過單一契約來源.
- code-memory MCP 預設是 Serena, 每個 wrapped session 都會註冊, 屬於固定要付的 context
  成本. 要關掉用 `--code-memory none`. 這個 MCP 由 wrap 註冊, 不由本 repo 部署或版控.

### 每次 wrap 都會清除舊 context tool 的殘留

v0.34 不只是拒絕舊旗標: 每一次 `headroom wrap` 與 `headroom unwrap` 都會呼叫
`purge_context_tool_artifacts()` 主動刪除舊版裝過的東西 (best-effort, 失敗不擋啟動,
報告寫 stderr). 刪除範圍包含 `~/.claude/settings.json` 與 `~/.cursor/hooks.json` 裡
命令含 `rtk-rewrite` / `rtk rewrite` / `lean-ctx-rewrite` / `lean-ctx-redirect` /
`lean-ctx hook` 的 hook, `~/.claude/hooks/` 下對應的 script 與 `.lean-ctx.bak`,
`~/.claude.json` 裡名為 `rtk` / `lean-ctx` 的 MCP entry, 各 hint 檔中
`<!-- headroom:rtk-instructions -->` 圍起來的區塊 (含**當前工作目錄**的那份), 以及

- `~/.local/bin/{rtk,lean-ctx}` — 只在它是指向 Headroom 自己 bin 目錄的 symlink 時,
- `~/.headroom/bin/{rtk,lean-ctx}` — **無條件刪除**.

本 repo 註冊的 hook 命令是 `rtk hook claude`, 不含上列任何 marker, 所以不會被誤刪
(2026-08-10 對 0.34 原始碼再次核對). 但**二進位檔會**: 若機器上的 `rtk` 是早期
Headroom 裝的 (`~/.local/bin/rtk` 指向 `~/.headroom/bin/rtk`), 下一次 `hclaude` 或
`hcodex` 就會把它連同 symlink 一起刪掉. hook 的 `command -v rtk` 前置檢查會讓它安靜地
變成 no-op — RTK 整個消失而不報錯. 因此 rtk 必須改由**與 Headroom 無關**的來源安裝
(見 `docs/setup.md`), 並用 `which -a rtk` 確認解析到的不是 `~/.local/bin/rtk`.

`headroom doctor` 回報 Codex routed, 只證明當下 shell environment 或
`~/.codex/config.toml` 的 machine-local 狀態; 不代表本 repo 的預設, 也不證明 Codex
App/Desktop 走相同路徑. Codex App 不在目前已驗證的 wrap surface.

## 元件與 owner

| 元件 | Owner | 邊界 |
|---|---|---|
| Proxy | Claude/Codex/Antigravity 都以明確的 `headroom wrap <agent>` session 為標準 | 只壓縮實際經 proxy 的流量 |
| Headroom MCP | `headroom mcp install` | 手動壓縮與 marker retrieval, 不等於全流量代理 |
| Coding compressor | Headroom stable release | 以具日期的 release notes 與安裝版本 capability 為準, 不在無日期段落固定 backend |
| RTK 指引 | harness 的 Claude/Codex contract | v0.34 起 Headroom 已不注入; `--serena-instructions` 維持關閉 |
| Serena code-memory | `headroom wrap` 的預設 (`--code-memory`) | 由 wrap 註冊 MCP, 不由本 repo 部署或版控 |
| Headroom plugin | 維持停用 (`headroom@headroom-marketplace`) | 避免與 CLI/MCP 的 lifecycle 重複 |

Claude App 使用 OAuth 直連, 不經 proxy, 只能透過 MCP 做手動文字壓縮. Codex App
尚未驗證, 不得沿用 Codex CLI 的 routing 結論. 圖片自動壓縮只存在 proxy 路徑.

## 操作指引

- **Claude**: 需要 Headroom 時使用 `hclaude`; Auto Mode 使用 `hclaude-auto`. 底層是 `headroom wrap claude`. 只有 context 明確不足時才加 `--1m`, 而且加之前要先讀下面那條.
- **`--1m` 的預設模型陷阱**: 自訂 `ANTHROPIC_BASE_URL` 之下, Claude Code 的 `/model` 選擇不會傳到 API, 只有帶 `[1m]` 後綴的 model id 才會送出 `context-1m` beta header. `--1m` 的做法是在啟動的 process 上設 `ANTHROPIC_MODEL`; 它會保留使用者自己設過的 model, 但 `ANTHROPIC_MODEL` 未設時退回 Headroom 內建的常數 (0.34.0 是 `claude-opus-4-8`). 也就是在乾淨 shell 直接下 `--1m` 會把 session 釘在 Opus 4.8 而不是當前選的模型. 要用就自己一起指定 `ANTHROPIC_MODEL`, 並在 session 內確認實際 model id.
- **on-demand tool loading (`--tool-search`)**: 自訂 `ANTHROPIC_BASE_URL` 會讓 Claude Code 關閉 tool deferral, 改成一次載入所有 tool schema, 吃掉數十 K 的 local context (upstream issue #746). v0.34 的 `wrap claude` 因此會設 `ENABLE_TOOL_SEARCH`, 預設 `true`. 可用值 `true`/`1`/`yes`/`on`, `false`/`0`/`no`/`off`, `auto`, `auto:N` (N 為 0-100); 打錯會直接報錯而不是默默關掉. 優先序是 `--tool-search` 旗標 > 環境裡既有的 `ENABLE_TOOL_SEARCH` (原封不動) > 內建預設; 空字串視同未設. Read/Edit/Bash 這類內建工具永遠不會被延後載入, agent loop 不受影響. 若採 always-on routing (下面的 `persistent-service`), 這個變數要跟 base URL 一起常駐, 否則原生 `claude` 會在沒有 deferral 的情況下走 proxy.
- **Codex**: 需要 Headroom 時使用 `hcodex`; Auto Mode 使用 `hcodex-auto`. 底層是 `headroom wrap codex`, 不依賴預先存在的永久 provider.
- **Antigravity CLI**: 原生 Auto Mode 使用 `agy-auto` (`agy --mode accept-edits`). Headroom 入口保留為 `hagy`/`hagy-auto`, 但會先確認安裝版本真的提供 `headroom wrap agy`; 沒有就 exit 127, 不能降級成未壓縮的 `agy`.
- **權限**: 一般自動執行分別使用 Claude `--permission-mode auto`, Codex `-a on-request -s workspace-write`, Antigravity `--mode accept-edits`. `--dangerously-skip-permissions` 與 `--dangerously-bypass-approvals-and-sandbox` 不是 Auto Mode, 也不是 Headroom 的必要參數; 只有外層已有隔離環境時才能針對單次任務明確選用. 可重用的 shell functions 見 `docs/setup.md`.
- **選用常駐 runtime**: `headroom install apply --preset persistent-service` 只供使用者明確選擇 always-on provider routing 的情境, 不是本 repo 預設, 也不是快速指令的前置依賴. profile, target, port 與 provider 設定均屬 machine-local state.
- **Preset lifecycle**:

  | Preset | Lifecycle | 升級與轉換 |
  |---|---|---|
  | `persistent-service` | 支援 `headroom install {status,start,stop,restart,remove}` | 套件升級後用 `restart` 讓常駐行程載入新版; 若 supervisor, manifest 或啟動參數有變, 重新執行 `headroom install apply` |
  | `persistent-task` | 排程只負責定期 ensure; 不支援 `start`, `stop`, `restart` | 不得以 `restart` 當升級路徑; 改以原本需要的 runtime, scope, provider, port, backend, mode 與 telemetry 選項重新 `apply --preset persistent-service`, 或重新 `apply --preset persistent-task` |

  從 `persistent-task` 轉換時, 先確認原 profile 的預期設定, 再以相同選項重新
  `headroom install apply`, 只把 `--preset` 改為 `persistent-service`. 不要只複製別台
  機器的 profile, port 或 provider 值.
- **套件管理**: CLI 由 `uv tool` 與 uv 管理的 Python 提供, `~/.local/bin/headroom` 是 MCP 設定應使用的絕對路徑.
- **升級**: 先執行 `headroom update --check`, 再用 `headroom update` 或 `uv tool upgrade headroom-ai`. 升級後重開 wrapped session; `persistent-service` profile 執行 `headroom install restart --profile <profile>`, 再以 `headroom install status --profile <profile>` 確認 `running` 與 `Healthy: yes`. `headroom doctor` 另用來確認 CLI, proxy 與 routing; 它不能取代 deployment health. `persistent-task` 依上表重新 `apply` 或先轉為 `persistent-service`. 若這次升級改動了 `headroom wrap` 的參數, 還要重跑 `scripts/install-zsh-functions.sh --apply`: `~/.zshrc` 裡的舊 block 不會自己更新, `hclaude`/`hcodex` 會帶著失效旗標啟動而被 CLI 擋下.
- **Legacy Codex provider**: v0.34 的 `headroom unwrap codex` 只認得目前的 auto-injected marker. 本機舊版 `# --- Headroom persistent provider ---` block 曾出現 CLI 宣稱成功但檔案未變; 必須直接檢查 `~/.codex/config.toml` 並以 `headroom doctor` 交叉驗證, 不得只採信成功訊息.
- **`headroom learn`**: 預設只允許寫入 machine-local, gitignored 的學習檔. 不得未經 review 直接以 `--target CLAUDE.md`, `AGENTS.md` 或其他 tracked contract 覆寫專案規則.
- **App 手動壓縮**: 只壓大型 read-only JSON, log, table 或 search output; 程式碼, 錯誤, 圖片與可編輯內容交給原始工具.

## 版本轉換

本機安裝的 v0.34.0 仍沒有 `headroom wrap agy`; 過去的上游
[PR #1044](https://github.com/headroomlabs-ai/headroom/pull/1044)
曾以限定 Google Cloud Code host 的 process-scoped TLS MITM 提案. 不要用無效 base URL
環境變數, 修改 `/etc/hosts`, 信任 system-wide CA, 或未 review 的 branch 假裝完成整合.
後續 stable release 若加入 `agy`, 須重新驗證 capability probe, MCP config path,
interactive/print mode, CA trust boundary, macOS 與本文件.

行動規則以 `headroom-protocol` skill 為準; 本文件只解釋 runtime 邊界.
