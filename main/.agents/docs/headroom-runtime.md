# Headroom Runtime Guide

> 只記錄跨機器的架構、操作邊界與版本轉換。venv、PID、port 與 profile 名稱屬 machine-local state，不進 git。

## 專案採用方式

本專案採 **wrap-first、session-scoped**：快速指令明確建立 Headroom session；原生
agent 指令維持直連或使用者自己的 machine-local 狀態。

| Surface | 標準入口 | 行為 |
|---|---|---|
| Claude Code 原生 session | `claude` | 直連 Anthropic，保留 Remote Control |
| Claude Code Headroom session | `headroom wrap claude --no-context-tool` | 只在這個 session 注入 `ANTHROPIC_BASE_URL`；Remote Control 不可用 |
| Codex 原生 session | `codex` | 使用當下 machine-local 設定；本 repo 不建立永久 Headroom provider |
| Codex Headroom session | `headroom wrap codex --no-context-tool` | 由 wrapper 建立該次 session 所需的 proxy 與 provider routing |
| Antigravity CLI 原生 session | `agy` | 直連 Google Cloud Code Assist |
| Antigravity CLI Headroom session | `headroom wrap agy` | 需要 Headroom 原生 `agy` adapter；未支援時 `hagy` 必須 fail closed，不得靜默直連 |
| Headroom MCP | `headroom mcp install --agent <agent> --proxy-url http://127.0.0.1:8787` | 提供 marker retrieve、compress 與 stats；實際可用 agent 以安裝版本的 registrar 為準 |

不得把 `ANTHROPIC_BASE_URL`、`OPENAI_BASE_URL` 或其他 provider endpoint 永久寫入
shell profile 或 git-tracked agent settings。RTK 指引由 harness 契約管理，因此 Claude
與 Codex wrap 都加 `--no-context-tool`，避免 Headroom 改寫 `AGENTS.md` 或 `CLAUDE.md`。
Antigravity 的上游 adapter 目前沒有這個選項，不得把未知參數假裝成已支援。

`headroom doctor` 回報 Codex routed，只證明當下 shell environment 或
`~/.codex/config.toml` 的 machine-local 狀態；不代表本 repo 的預設，也不證明 Codex
App／Desktop 走相同路徑。Codex App 不在目前已驗證的 wrap surface。

## 元件與 owner

| 元件 | Owner | 邊界 |
|---|---|---|
| Proxy | Claude／Codex／Antigravity 都以明確的 `headroom wrap <agent>` session 為標準 | 只壓縮實際經 proxy 的流量 |
| Headroom MCP | `headroom mcp install` | 手動壓縮與 marker retrieval，不等於全流量代理 |
| Coding compressor | Headroom stable release | v0.32.1 以 tokensave 為主、Serena 為 fallback |
| RTK 指引 | harness 的 Claude／Codex contract | Headroom wrap 不得重複注入 |
| Headroom plugin | 維持停用（`headroom@headroom-marketplace`） | 避免與 CLI／MCP 的 lifecycle 重複 |

Claude App 使用 OAuth 直連，不經 proxy，只能透過 MCP 做手動文字壓縮。Codex App
尚未驗證，不得沿用 Codex CLI 的 routing 結論。圖片自動壓縮只存在 proxy 路徑。

## 操作指引

- **Claude**：需要 Headroom 時使用 `hclaude`；Auto Mode 使用 `hclaude-auto`。底層是 `headroom wrap claude --no-context-tool`。只有 context 明確不足時才加 `--1m`。
- **Codex**：需要 Headroom 時使用 `hcodex`；Auto Mode 使用 `hcodex-auto`。底層是 `headroom wrap codex --no-context-tool`，不依賴預先存在的永久 provider。
- **Antigravity CLI**：原生 Auto Mode 使用 `agy-auto`（`agy --mode accept-edits`）。Headroom 入口保留為 `hagy`／`hagy-auto`，但會先確認安裝版本真的提供 `headroom wrap agy`；沒有就 exit 127，不能降級成未壓縮的 `agy`。
- **權限**：一般自動執行分別使用 Claude `--permission-mode auto`、Codex `-a never -s workspace-write`、Antigravity `--mode accept-edits`。`--dangerously-skip-permissions` 與 `--dangerously-bypass-approvals-and-sandbox` 不是 Auto Mode，也不是 Headroom 的必要參數；只有外層已有隔離環境時才能針對單次任務明確選用。可重用的 shell functions 見 `docs/setup.md`。
- **選用常駐 runtime**：`headroom install apply --preset persistent-service` 只供使用者明確選擇 always-on provider routing 的情境，不是本 repo 預設，也不是快速指令的前置依賴。profile、target、port 與 provider 設定均屬 machine-local state；使用者自行以 `headroom install {status,start,stop,restart,remove}` 維護。
- **套件管理**：CLI 由 `uv tool` 與 uv 管理的 Python 提供，`~/.local/bin/headroom` 是 MCP 設定應使用的絕對路徑。
- **升級**：先執行 `headroom update --check`，再用 `headroom update` 或 `uv tool upgrade headroom-ai`。升級後重開 wrapped session；若使用者另有 persistent profile 才 restart，最後用 `headroom doctor` 確認 CLI 與 proxy 版本一致。
- **`headroom learn`**：預設只允許寫入 machine-local、gitignored 的學習檔。不得未經 review 直接以 `--target CLAUDE.md`、`AGENTS.md` 或其他 tracked contract 覆寫專案規則。
- **App 手動壓縮**：只壓大型 read-only JSON、log、table 或 search output；程式碼、錯誤、圖片與可編輯內容交給原始工具。

## 版本轉換

PyPI v0.32.1 仍以 tokensave 為預設，現況正確。這個版本沒有
`headroom wrap agy`；上游 [PR #1044](https://github.com/headroomlabs-ai/headroom/pull/1044)
以限定 Google Cloud Code host 的 process-scoped TLS MITM 實作，但仍未合併。不要用無效
base URL 環境變數、修改 `/etc/hosts`、信任 system-wide CA，或未 review 的 branch 假裝完成
整合。下一個 stable release 若加入 `agy`，須重新驗證 capability probe、MCP config path、
interactive／print mode、CA trust boundary、macOS 與本文件。

行動規則以 `headroom-protocol` skill 為準；本文件只解釋 runtime 邊界。
