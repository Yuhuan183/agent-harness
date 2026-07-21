# agent-harness

跨 agent 的全域 harness 配置管理專案。把散落在 `~/.claude`、`~/.codex`、`~/.agents`
的手寫配置納入版控，作為「蒸餾—瘦身—回寫」的工作區，讓全域指令檔維持在最小常駐負載。

## 結構

每個 harness 目錄各有自己的 README（點進去看該層的完整索引與邊界）。

| 目錄 | 內容 | 對應全域位置 | 說明 |
| --- | --- | --- | --- |
| [`.claude/`](.claude/README.md) | Claude Code 契約：`CLAUDE.md`、`agents/`、自有 skills、`hooks/`、`prompts/`、`settings.json`… | `~/.claude/` | 見 `.claude/README.md` |
| [`.codex/`](.codex/README.md) | Codex 契約：`AGENTS.md`、`prompts/`、`agents/`、可攜 `config.merge.toml` | `~/.codex/` | 見 `.codex/README.md` |
| [`.agents/`](.agents/README.md) | 跨 agent 共用層：共用 skill 本體、跨 agent runtime 知識、第三方套件清單 | `~/.agents/` | 見 `.agents/README.md` |
| [`docs/`](docs/) | 專案知識層：方法論、研究、決策紀錄、套用說明 | —（不回寫全域） | 見下 |

## 文檔職責（兩層）

**專案知識層 `docs/`** — 關於 harness engineering 學科與如何維運本 repo 的知識，
給「在 agent-harness 上工作的人／agent」讀，**不回寫全域**：

| 檔案 | 職責 |
| --- | --- |
| [`docs/harness-engineering.md`](docs/harness-engineering.md) | 跨專案方法論 playbook（統一維護版） |
| [`docs/harness-engineering-research.md`](docs/harness-engineering-research.md) | 佐證數據與研究報告連結 |
| [`docs/global-claude-md-slimming.md`](docs/global-claude-md-slimming.md) | 全域 CLAUDE.md 瘦身的逐區塊決策與驗收 |
| [`docs/setup.md`](docs/setup.md) | 把配置套用到全域的流程、驗收與回滾 |

**可攜配置層 `.claude/` `.codex/` `.agents/`** — 實際的 agent 配置，**會回寫全域**，
每層以自己的 README 描述內容與邊界。共用 skill 本體只在 `.agents/`，另兩層以相對
symlink 引用（避免重複）。跨 agent runtime 知識（如 Headroom）也在 `.agents/docs/`，
不在單一 agent 目錄下各留一份。

## 工作方式

1. 在本專案內編修配置（可 diff、review、回滾）。
2. `scripts/sync.sh` dry-run 檢視 → `--apply` 回寫全域（自動備份；codex `config.toml`
   僅手動 merge）。完整流程與驗收見 [`docs/setup.md`](docs/setup.md)。
3. 只納入手寫的可攜契約——機器狀態（`.codex/config.toml`、`.claude/mcp_servers.json`
   的本機路徑段、sessions、cache、history、auth 憑證）一律不入庫，改以 `*.merge.*` /
   `examples/` 範例手動 merge。

## License

[MIT](LICENSE)。此 repo 為個人 harness 配置與方法論；MIT 允許自由取用與改寫，僅保留著作權聲明。
