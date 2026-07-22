# Headroom Runtime Guide

> 只記錄跨機器的架構與操作邊界。版本、venv、PID 與本機故障史屬 machine-local state，不進本文件。
> 對照官方 v0.32:`headroom wrap` 是推薦的預設入口；`headroom install`(launchd/systemd 常駐)為選用的常駐替代方案。兩者皆自動管理 base URL 路由，**不需**手動改 agent settings。

## 兩種路由模式

| 模式 | 指令 | 適用 | 邊界 |
|---|---|---|---|
| **Wrap(推薦預設)** | `headroom wrap claude --tool-search true` | 個人、逐 session;proxy 只在 wrapped session 內起，結束即 idle/down 屬正常 | routing 由 wrapper 自動設定，session-scoped;tracked settings 不留 base URL |
| **Persistent install(選用)** | `headroom init` / `headroom install apply`(supervisor=task → launchd) | 想要跨 session 常駐、隨開即用 | routing 仍 machine-local(shell profile export 或部署自帶);tracked settings 一樣不留 base URL |

兩模式共用同一原則：**base URL 是 machine-local,永不進 git-tracked 的 `settings.json`**(否則在沒有 proxy 的機器上 clone 會指向死掉的 localhost)。健康檢查用 `headroom doctor`。

## 元件與 owner

| 元件 | Owner | 邊界 |
|---|---|---|
| Proxy `:8787` | wrap 模式由 `headroom wrap claude` 起；persistent 模式由部署 supervisor 起 | 只壓縮實際經 proxy 的 CLI／Codex 流量；tracked settings 不永久改 base URL |
| CCR MCP | Wrapper 或 `headroom mcp install --agent claude` | 手動 compress/retrieve/stats 與 marker retrieval |
| `tokensave` | Wrapper 的 machine-local 設定 | 程式碼語意壓縮；與 CCR MCP 不重複 |
| Headroom plugin | 維持停用(`headroom@headroom-marketplace`) | 其 durable ensure lifecycle 會與上述模式重複，勿啟用 |

Claude App 使用 OAuth 直連，不經 proxy;只可使用 MCP 做手動文字壓縮。圖片的自動壓縮也只存在 proxy 路徑。

## 操作指引

- **標準入口(wrap)**:`headroom wrap claude --tool-search true`。只有標準 context 明確不足才加 `--1m`。Wrapper session 結束後 proxy idle/down 屬正常。
- **常駐替代(persistent)**:`headroom install apply` 建立部署；`persistent-task` preset(supervisor=none)以 `headroom install {status,stop,start,restart} --profile <name>` 管理。launchd-supervised 部署另可用 `launchctl kickstart -k "gui/$(id -u)/com.headroom.<profile>"` 立即重載。base URL 仍靠 machine-local 的 shell profile export,不寫進 tracked settings。
- **套件管理**:headroom CLI 由 `uv tool` 管理，並綁 uv 自管 Python(`uv python install`),與 Homebrew 的 Python formula 脫鉤——避免 `brew autoremove` 連帶移除 interpreter 而使 venv 失效。`~/.local/bin/headroom` 為 uv 建立的 shim。
- **升級**:proxy 是長壽命行程，升級套件後需重載才生效 ——(1) `uv tool upgrade headroom-ai`(取代不穩定的 `headroom update` 內建自檢);(2) 結束舊 wrapped session 重開，或對 persistent 部署 `headroom install restart --profile <name>`。以 `headroom doctor` 驗證 `version` 列(proxy 版本須與 installed 相符)。
- **App 手動壓縮**:只壓大型 read-only JSON、log、table 或 search output;程式碼、錯誤、圖片、可編輯內容交給原始工具。
- 行動規則以 `headroom-protocol` skill 為準；本文件只解釋 runtime 邊界。
