# `.codex/` — Codex Harness 契約

可跨機器共用的 Codex／ChatGPT 配置，回寫到 `~/.codex/`。
與 `.claude/` 平行；跨 agent 共用知識與 skill 本體在 `../.agents/`。

## 內容索引

| 路徑 | 職責 | 同步 |
|---|---|---|
| `AGENTS.md` | Codex 全域工作契約（45 行已審核可攜版：outcome-first、最小 scope、direct-first dispatch、風險觸發的獨立驗證） | 自動 |
| `agents/verifier.toml` | Codex 獨立 verifier 角色定義 | 自動 |
| `skills/headroom-protocol` | symlink → `../.agents/skills/headroom-protocol`（與 Claude 共用同一本體） | 自動 |
| `prompts/custom-instructions.md` | ChatGPT App chat 模式的 custom instructions | 自動 |
| `config.merge.toml` | 可攜設定片段（model／effort 等），**手動** merge 進 `~/.codex/config.toml` | 手動 |
| `config.toml` | 機器狀態（headroom proxy、marketplace、trust、project 路徑等 machine-local 段）；**不入庫**（gitignored），僅存在本機 | 不覆蓋 |
| `ANALYSIS.md`, `DEPLOY.md` | Codex／ChatGPT 蒸餾結論與跨機器部署流程 | 自動 |

## 邊界

`config.toml` 是機器狀態（base URL、憑證路徑、marketplace 來源、PID 等），
**永不自動覆蓋**；跨機器只透過 `config.merge.toml` 帶可攜設定，套用方式見 `DEPLOY.md`。
`~/.codex/skills/headroom-protocol` 回寫後應為指向 `~/.agents/` 的 symlink（`sync.sh` 以
`--force` 將既有實體目錄替換為連結）。
