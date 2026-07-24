# Headroom Runtime Guide

> 只記錄跨機器的架構、操作邊界與版本轉換。venv、PID、port 與 profile 名稱屬 machine-local state，不進 git。

## 專案採用方式

| Surface | 標準入口 | 行為 |
|---|---|---|
| Claude Code 原生 session | `claude` | 直連 Anthropic，保留 Remote Control |
| Claude Code Headroom session | `headroom wrap claude --no-context-tool` | 只在這個 session 注入 `ANTHROPIC_BASE_URL`；Remote Control 不可用 |
| Codex | machine-local `config.toml` Headroom provider | Codex WebSocket 路由不能只靠 `OPENAI_BASE_URL`，provider 設定不納入同步 |
| Claude／Codex MCP | `headroom mcp install --agent <agent> --proxy-url http://127.0.0.1:8787` | 提供 marker retrieve、compress 與 stats；installer 管理 machine-local 絕對路徑 |

不得把 `ANTHROPIC_BASE_URL` 或 `OPENAI_BASE_URL` 永久寫入 shell profile 或 git-tracked agent settings。RTK 指引由 harness 契約管理，因此所有 wrap 指令都加 `--no-context-tool`，避免 Headroom 改寫 `AGENTS.md` 或 `CLAUDE.md`。

## 元件與 owner

| 元件 | Owner | 邊界 |
|---|---|---|
| Proxy | `headroom wrap`，或選用的 `headroom deploy` supervisor | 只壓縮實際經 proxy 的流量 |
| Headroom MCP | `headroom mcp install` | 手動壓縮與 marker retrieval，不等於全流量代理 |
| Coding compressor | Headroom stable release | v0.32.1 以 tokensave 為主、Serena 為 fallback |
| RTK 指引 | harness 的 Claude／Codex contract | Headroom wrap 不得重複注入 |
| Headroom plugin | 維持停用（`headroom@headroom-marketplace`） | 避免與 CLI／MCP 的 lifecycle 重複 |

Claude App 使用 OAuth 直連，不經 proxy，只能透過 MCP 做手動文字壓縮。圖片自動壓縮只存在 proxy 路徑。

## 操作指引

- **Claude**：日常使用 `claude`；需要 Headroom 時才使用 `headroom wrap claude --no-context-tool`。只有 context 明確不足時才加 `--1m`。
- **Codex**：使用 machine-local Headroom provider。若從 wrap 啟動，使用 `headroom wrap codex --no-context-tool`；不得把 `--dangerously-bypass-approvals-and-sandbox` 寫入 alias、profile 或固定啟動流程。
- **權限**：一般自動執行分別使用 Claude `--permission-mode auto` 與 Codex `-a never -s workspace-write`。`--dangerously-skip-permissions` 與 `--dangerously-bypass-approvals-and-sandbox` 不是 Auto Mode，也不是 Headroom 的必要參數；只有外層已有隔離環境時才能針對單次任務明確選用。可重用的 shell functions 範例見 `docs/setup.md`。
- **常駐 runtime**：新部署使用 `headroom deploy`；後續以 `headroom install {status,start,stop,restart,remove} --profile <name>` 管理。不要用 supervisor=`none` 的孤兒程序取代可觀測的生命週期。
- **套件管理**：CLI 由 `uv tool` 與 uv 管理的 Python 提供，`~/.local/bin/headroom` 是 MCP 設定應使用的絕對路徑。
- **升級**：先執行 `headroom update --check`，再用 `headroom update` 或 `uv tool upgrade headroom-ai`。升級後重開 wrapped session，或 restart persistent profile，最後用 `headroom doctor` 確認 CLI 與 proxy 版本一致。
- **`headroom learn`**：預設只允許寫入 machine-local、gitignored 的學習檔。不得未經 review 直接以 `--target CLAUDE.md`、`AGENTS.md` 或其他 tracked contract 覆寫專案規則。
- **App 手動壓縮**：只壓大型 read-only JSON、log、table 或 search output；程式碼、錯誤、圖片與可編輯內容交給原始工具。

## 版本轉換

PyPI v0.32.1 仍以 tokensave 為預設，現況正確。上游 `main` 已改為 Serena 預設，但尚未發布；不要為此安裝未發布的 branch。下一個 stable release 升級時，讓 Headroom 執行其 migration，並重新驗證 MCP、code graph 與本文件。

行動規則以 `headroom-protocol` skill 為準；本文件只解釋 runtime 邊界。
