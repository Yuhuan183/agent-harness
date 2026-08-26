# Headroom Runtime Guide

> **本機版本查核不寫在這裡, 這是刻意的.** 這是共用 repo, 而每個部署各有自己的版本 ——
> 一則「本機 CLI 是 X」在寫它的那台是事實, 在別台就是假話, 而讀的人分不出來. 2026-08-20
> 那批紀錄正是這樣出事的: 兩個部署的觀察被寫成同一個「本機」, 然後拿其中一台的 log 去
> 撤回另一台的真實紀錄. 原文留在 Git 歷史與
> [landing-log](../../../docs/research/landing-log.md), 那裡的職責就是記錄推翻的過程.
>
> 要知道你這台在跑什麼, **當場問四個來源**, 而且第四個不能是問 CLI 得來的:
>
> ```bash
> headroom --version                                   # CLI
> uv tool list | grep headroom                         # 裝了什麼
> curl -s http://127.0.0.1:8787/health                 # 跑著的 proxy 自報
> grep "Proxy started" ~/.headroom/logs/proxy.log*     # 啟動橫幅 (旁證)
> ```
>
> 前三個都可能一致地錯 —— 升級了 CLI 卻沒 `headroom install restart`, 三者會有兩者說新版
> 而實際跑的是舊的. 啟動橫幅是唯一不經由 CLI 的紀錄, 也是唯一能把 uptime 對上的.
>
> **本 repo 只跟當前 Headroom.** 這份文件寫的是當前版本的行為, 不寫版本下限, 也不寫
> 「哪一版開始有什麼」的遷移史. 停在舊版的機器要自己調配 —— 維護那張對照表的成本落在
> 每一個讀的人身上, 而收益只有停在舊版的那一台拿得到. 裝了 Headroom 就是前提, 版本不是.

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
RTK 指引由 harness 契約管理. Headroom 沒有
CLI context tools, 因此 Claude 與 Codex wrap 不傳入那類選項; 舊旗標會被 CLI 明確拒絕
並附遷移訊息, 不是被忽略.

注入入口有兩個預設值, 兩者都要知道:

- `--serena-instructions` 預設關閉, 本 repo 不啟用. 它會把 marker-fenced 區塊寫進
  **當前工作目錄**的 `CLAUDE.md` 或 `AGENTS.md`; 在本 repo 根目錄執行等於憑空生出一份
  會被 Claude Code 載入的專案指引, 繞過單一契約來源.
- code-memory MCP 預設是 Serena, 每個 wrapped session 都會註冊, 屬於固定要付的 context
  成本. 要關掉用 `--code-memory none`. 這個 MCP 由 wrap 註冊, 不由本 repo 部署或版控.

### 每次 wrap 都會清除舊 context tool 的殘留

不只是拒絕舊旗標: 每一次 `headroom wrap` 與 `headroom unwrap` 都會呼叫
`purge_context_tool_artifacts()` 主動刪除舊版裝過的東西 (best-effort, 失敗不擋啟動,
報告寫 stderr). 刪除範圍包含 `~/.claude/settings.json` 與 `~/.cursor/hooks.json` 裡
命令含 `rtk-rewrite` / `rtk rewrite` / `lean-ctx-rewrite` / `lean-ctx-redirect` /
`lean-ctx hook` 的 hook, `~/.claude/hooks/` 下對應的 script 與 `.lean-ctx.bak`,
`~/.claude.json` 裡名為 `rtk` / `lean-ctx` 的 MCP entry, 各 hint 檔中
`<!-- headroom:rtk-instructions -->` 圍起來的區塊 (含**當前工作目錄**的那份), 以及

- `~/.local/bin/{rtk,lean-ctx}` — 只在它是指向 Headroom 自己 bin 目錄的 symlink 時,
- `~/.headroom/bin/{rtk,lean-ctx}` — **無條件刪除**.

本 repo 註冊的 hook 命令是 `rtk hook claude`, 不含上列任何 marker, 所以不會被誤刪
(核對紀錄見 [`RTK.md`](../../claude/RTK.md)). 但**二進位檔會**: 若機器上的 `rtk` 是早期
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
| RTK 指引 | harness 的 Claude/Codex contract | Headroom 不注入; `--serena-instructions` 維持關閉 |
| Serena code-memory | `headroom wrap` 的預設 (`--code-memory`) | 由 wrap 註冊 MCP, 不由本 repo 部署或版控 |
| Headroom plugin | 維持停用 (`headroom@headroom-marketplace`) | 避免與 CLI/MCP 的 lifecycle 重複 |

Claude App 使用 OAuth 直連, 不經 proxy, 只能透過 MCP 做手動文字壓縮. Codex App
尚未驗證, 不得沿用 Codex CLI 的 routing 結論. 圖片自動壓縮只存在 proxy 路徑.

## 操作指引

- **Claude**: 需要 Headroom 時使用 `hclaude`; Auto Mode 使用 `hclaude-auto`. 底層是 `headroom wrap claude --1m`, 2026-08-21 起**預設就是 1M context**, 見下面兩條.
- **`--1m`**: 自訂 `ANTHROPIC_BASE_URL` 之下, Claude Code 的 `/model` 選擇不會傳到 API,
  只有帶 `[1m]` 後綴的 model id 才會送出 `context-1m` beta header; 不加 `--1m` 就是 200k.
  wrapper 端沒設 `ANTHROPIC_MODEL` 時會退到內建預設 `claude-opus-5`, 可用
  `HEADROOM_1M_MODEL` 逐 shell 覆寫; 已設的 `ANTHROPIC_MODEL` 只會被補上後綴, 而且是冪等的.
  proxy 端會把 `[1m]` 算進 context budget 再計價.
- **旗標位置是關鍵, 不要「整理」它.** `--` 之後的東西全部歸 `claude_args`, 所以 `--1m` 必須
  在 `--` 之前. 對真正的 command object 實測: `['--1m', ...]` 得到 `context_1m=True`, 而
  `['--', '--1m', ...]` 得到 `False`, 並把旗標原樣交給 `claude` 執行檔 —— session 靜靜地停在
  200k, 沒有任何錯誤訊息. 2026-08-21 之前 `hclaude` 正是後者.

  代價是沒設過 `ANTHROPIC_MODEL` 時, session 會被釘在 Headroom 的預設 `claude-opus-5`, 要換
  就用 `HEADROOM_1M_MODEL`. 另一條路是在 `~/.zshrc` 設
  `ANTHROPIC_MODEL="claude-opus-5[1m]"` (wrap 用 `os.environ.copy()`, 所以會生效), 但那會
  釘死每一個 session 並讓 `/model` 選單失效 —— upstream #2983 明講這是它要取代的 workaround,
  不建議.
- **沒有 1M→200k 的降級階梯.** release note 的 “make `--1m` fallback model configurable” 指的是「未指定 model 時要用哪個 model」, 不是 context 大小的 fallback. `[1m]` 是向 Anthropic 請求 1M tier, 有沒有資格是帳號層級的事; 沒資格就是 API 報錯, 不會自動退回 200k.
- **on-demand tool loading (`--tool-search`)**: 自訂 `ANTHROPIC_BASE_URL` 會讓 Claude Code
  關閉 tool deferral, 改成一次載入所有 tool schema, 吃掉數十 K 的 local context
  (upstream issue #746). `wrap claude` 因此會設 `ENABLE_TOOL_SEARCH`, 預設 `true`.

  可用值是 `true`/`1`/`yes`/`on`, `false`/`0`/`no`/`off`, `auto`, `auto:N` (N 為 0-100);
  打錯會直接報錯, 不會默默關掉. 優先序是 `--tool-search` 旗標 > 環境裡既有的
  `ENABLE_TOOL_SEARCH` (原封不動) > 內建預設, 空字串視同未設. Read/Edit/Bash 這類內建工具
  永遠不會被延後載入, agent loop 不受影響. 若採 always-on routing (下面的
  `persistent-service`), 這個變數要跟 base URL 一起常駐, 否則原生 `claude` 會在沒有 deferral
  的情況下走 proxy.
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
- **升級**: 先執行 `headroom update --check`, 再用 `headroom update` 或
  `uv tool upgrade headroom-ai`. 升級後重開 wrapped session; `persistent-service` profile
  執行 `headroom install restart --profile <profile>`, 再以
  `headroom install status --profile <profile>` 確認 `running` 與 `Healthy: yes`.
  `headroom doctor` 另用來確認 CLI, proxy 與 routing, 但它不能取代 deployment health.
  `persistent-task` 依上表重新 `apply`, 或先轉為 `persistent-service`.

  這次升級若改動了 `headroom wrap` 的參數, 還要重跑 `scripts/install-zsh-functions.sh --apply`:
  `~/.zshrc` 裡的舊 block 不會自己更新, `hclaude`/`hcodex` 會帶著失效旗標啟動而被 CLI 擋下.
- **Legacy Codex provider**: `headroom unwrap codex` 只認得目前的 auto-injected marker. 本機舊版 `# --- Headroom persistent provider ---` block 曾出現 CLI 宣稱成功但檔案未變; 必須直接檢查 `~/.codex/config.toml` 並以 `headroom doctor` 交叉驗證, 不得只採信成功訊息.
- **`headroom learn`**: 預設只允許寫入 machine-local, gitignored 的學習檔. 不得未經 review 直接以 `--target CLAUDE.md`, `AGENTS.md` 或其他 tracked contract 覆寫專案規則.
- **App 手動壓縮**: 只壓大型 read-only JSON, log, table 或 search output; 程式碼, 錯誤, 圖片與可編輯內容交給原始工具.

## 升級之後

只跟當前版本, 所以升級的動作固定而短:

1. 升 CLI, 然後 `headroom install restart`. **不重啟的話 CLI 會說新版而跑的是舊的** ——
   而且 `headroom --version` 與 `uv tool list` 會一起這麼說, 三個來源裡有兩個一致地錯.
2. 對照 `headroom wrap claude --help` 的旗標面. 有變就重跑
   `scripts/install-zsh-functions.sh --apply` (它是冪等的, 且不在 `sync.sh` 裡).
3. 用開頭那四個來源確認, 第四個不能是問 CLI 得來的.

當前旗標面: `--1m --backend --code-graph --code-memory --learn --memory --no-mcp
--no-proxy --port --region --serena-instructions --tool-search`. `hclaude` 帶 `--1m`, 理由
見操作指引那兩條.

## CCR 串流與 `lossless` 開關

**你這台有沒有套用過, 要當場查, 不要從這裡推**:

```bash
cat ~/.headroom/settings.json 2>/dev/null || echo "沒套用過"
grep "Proxy started" -A12 ~/.headroom/logs/proxy.log | grep tool_injection
```

有 `{"lossless": true}` 就是套用過; banner 含 `tool_injection` 表示 CCR 是全開的預設狀態.
這兩件在不同部署上答案不同, 所以本文件不記錄任何一台的答案 —— 2026-08-20 就是有人記了,
而那個答案在另一台是相反的.

這節保留的理由是: 它是唯一寫下這個開關「設在哪, 怎麼查, 怎麼撤」的地方. 這個處置本來是
上游串流缺陷的暫時繞道, 而上游已經修掉串流本身 (#3092, #3094, #3102, #2953, #3142) ——
也就是下面那條撤除判準要求先確認的事.

**這是上游 bug 的暫時處置, 不由本 repo 管理.** 開關住在 machine-local 的
`~/.headroom/settings.json`, 與 profile, port 同級, 不進 git.

CCR (Compress-Cache-Retrieve) 壓掉大塊工具輸出, 留下 `<<ccr:...>>` marker, 並注入
`headroom_retrieve` 讓模型需要時取回原文 — 有損壓縮**加上**還原路徑. 這個開關存在的原因是
上游曾在遇到串流請求時把它改成非串流以便在伺服器端處理取回
(`ccr_streaming_retrieve_buffered_non_stream`), 而回吐給 client 的內容可能解析不了 ——
症狀是 HTTP 200 但 body 是空的或壞的. 上游已修掉串流本身; 這節留著是為了「開關設在哪,
怎麼查, 怎麼撤」.

處置用 `lossless` 而不是 `no-ccr`: 依上游自己的說明 `--no-ccr` 是 lossy compression with no
recovery path, 壓掉的工具輸出救不回來; lossless 只做無損轉換, 代價僅是省得比較少. 讀原始碼
確認它一次清掉 `ccr_inject_marker` 與 `ccr_inject_tool` — 沒有 marker, 也沒有工具可注入,
那條串流轉換就失去入口, 不是繞過它.

設在哪, 由部署形態決定:

| 部署形態 | 設在哪 |
|---|---|
| `persistent-service` 常駐 | `POST /settings` body `{"values": {"lossless": true}}`, 再 `headroom install restart`; 值落在 `~/.headroom/settings.json` |
| wrap-first | 該次 session 的環境變數 `HEADROOM_LOSSLESS=1` |

**環境變數只到得了「這次啟動的 proxy」.** port 上已有 proxy 時 `wrap` 直接重用它, 而它的功能
比對只看 memory / learn / code_graph / copilot / openai-api-url — lossless 不在清單裡, 於是
變數靜靜地沒作用. 2026-08-17 實測: 常駐服務在跑時 `hclaude` 重用了既有 proxy (PID 未變),
變數確實出現在 session 環境裡卻毫無效果. 優先序是 `環境變數 > settings.json > 內建預設`,
而常駐服務的行程環境沒有這個變數, 所以設定檔會贏.

怎麼看跑著的是哪個模式 — `/health` 沒有任何 CCR 欄位, 但不是查不到, 只是不在那裡:

| 看什麼 | 開著 CCR | lossless 生效 |
|---|---|---|
| `GET /settings` (loopback) | 沒有 `lossless` 鍵 | `{"lossless": true}` |
| 啟動 banner 的 `CCR (Compress-Cache-Retrieve): ENABLED (...)` | 含 `tool_injection` | **不含 `tool_injection`** |
| `proxy.log` | 出現 `ccr_streaming_retrieve_buffered_non_stream` | 不再出現 |

banner 仍會列 `response_handling`, `context_tracking`, `proactive_expansion` — **那不代表沒生效**,
lossless 只強制 `ccr_inject_tool` 為 false.

撤除: `{"values": {"lossless": false}}` 後重啟, 或直接刪掉該鍵. 撤除前先確認上游修的是串流那條
路徑, 不是只改了壓縮策略 — 兩者的 release note 讀起來很像.

### Antigravity CLI

Headroom 目前沒有 `headroom wrap agy` (`headroom wrap --help` 的 supported tools 清單無此項,
2026-08-21 確認);
上游 [PR #1044](https://github.com/headroomlabs-ai/headroom/pull/1044)
仍 open (2026-08-14 最後更新), 曾以限定 Google Cloud Code host 的 process-scoped
TLS MITM 提案. 不要用無效 base URL 環境變數, 修改 `/etc/hosts`, 信任 system-wide CA,
或未 review 的 branch 假裝完成整合.
後續 stable release 若加入 `agy`, 須重新驗證 capability probe, MCP config path,
interactive/print mode, CA trust boundary, macOS 與本文件.

行動規則以 `headroom-protocol` skill 為準; 本文件只解釋 runtime 邊界.
