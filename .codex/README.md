# `.codex/` — Codex Harness 契約

> 專案全貌與跨平台資料流見[根 README](../README.md)；方法、研究與部署指引見
> [docs/README.md](../docs/README.md)。

可跨機器共用的 Codex／ChatGPT 配置，回寫到 `~/.codex/`。
與 `.claude/` 平行；跨 agent 共用知識與 skill 本體在 `../.agents/`。

## 內容索引

| 路徑 | 職責 | 同步 |
|---|---|---|
| `AGENTS.contract.md` | Codex 全域工作契約源檔（部署為 `~/.codex/AGENTS.md`；改名避免在 .codex/ 內開 session 時重複載入）（outcome-first、最小 scope、direct-first dispatch、風險觸發的獨立驗證） | 自動 |
| `agents/*.toml` | 七個 Codex leaf 角色定義（鏡像 Claude roles） | 自動 |
| `model-routing.toml` | Codex main／leaf 的結構化 model-effort 先驗與 AA v4.1 快照 | 自動 |
| `scripts/model-routing` | 驗證品質門檻並解析 profile；共用核心在 `../.agents/scripts/routing_core.py`（缺失時報部署錯誤） | 自動 |
| `scripts/bridge-brief` | 從 Claude 派 Codex twin 時，產出含 resolved model/effort 與角色契約的 brief 骨架 | 自動 |
| `skills/leaf-dispatch` | Codex 原生派工細節（resolver 呼叫、brief 組裝、記帳）；主契約按需載入 | 自動 |
| `skills/headroom-protocol` | symlink → `../.agents/skills/headroom-protocol`（與 Claude 共用同一本體） | 自動 |
| `skills/experience-ledger` | symlink → `../.agents/skills/experience-ledger`（派工經驗記帳與分析，與 Claude 共用） | 自動 |
| `skills/speak-human-tw` | symlink → `../.agents/skills/speak-human-tw`（繁中去 AI 味，與 Claude 共用同一本體） | 自動 |
| `skills/task-observer` | symlink → `../.agents/skills/task-observer`（明確 opt-in 的 skill 改進觀察；machine-local JSONL） | 自動 |
| `prompts/custom-instructions.md` | ChatGPT App chat 模式的 custom instructions | 自動 |
| `config.merge.toml` | 可攜設定片段（model／effort 等），**手動** merge 進 `~/.codex/config.toml` | 手動 |
| `config.toml` | 機器狀態（headroom proxy、marketplace、trust、project 路徑等 machine-local 段）；**不入庫**（gitignored），僅存在本機 | 不覆蓋 |
| `ANALYSIS.md`, `DEPLOY.md` | Codex／ChatGPT 蒸餾結論與跨機器部署流程 | 自動 |

## 邊界

`config.toml` 是機器狀態（base URL、憑證路徑、marketplace 來源、PID 等），
**永不自動覆蓋**；跨機器只透過 `config.merge.toml` 帶可攜設定，套用方式見 `DEPLOY.md`。
`model-routing.toml` 只是可查詢的 dispatch 建議，不會改寫 `config.toml` 或目前 task；本機
`experience-ledger` 有足夠同角色／task class 樣本時，其可接受率、返工、時間與同口徑 token 證據優先；
native Codex 記錄來源為 `codex`，Claude bridge 為 `claude-code-plugin-codex`。
Main route 只供開啟 task 前選擇；執行中的 main 不會切換模型。Leaf route 依 resolver 的
`invocation` 使用 spawn argument；未來若啟用 Luna，才使用另行註冊的 custom agent config。切換模型時固定
`fork_turns = "none"`，由完整 brief 重建必要脈絡。部署後從 `${CODEX_HOME:-$HOME/.codex}/scripts/model-routing` 執行；repo 內則
使用 `.codex/scripts/model-routing`。模型可用性分為訂閱、main selector、原生 leaf override
與 Claude bridge override；訂閱可用不等於 leaf override 已驗證。Claude 經
`codex:codex-rescue` 派 Codex twin 時，也必須以 `--surface claude-bridge` 解析同一份 profile。
`~/.codex/skills/headroom-protocol` 回寫後應為指向 `~/.agents/` 的 symlink（`sync.sh` 以
`--force` 將既有實體目錄替換為連結）。
