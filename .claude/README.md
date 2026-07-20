# `.claude/` — Claude Code Harness 契約

可跨機器共用的 Claude Code／Cowork 配置，回寫到 `~/.claude/`。Git 僅保存規則與可攜機制；
憑證、對話紀錄、遙測、快取、MCP 執行狀態與機器路徑皆留在本機。
套用到全域：專案根 `scripts/sync.sh`。

## 內容索引

| 路徑 | 職責 |
|---|---|
| `CLAUDE.md` | Claude Code 執行契約；僅主 agent 使用的精簡協調規則（~600 tokens） |
| `agents/` | 七個自足的 Claude leaf roles（effort 兩階：機械角色鎖 low、思考角色跟隨主 session，上限 high）；不讀取主 agent 協調文件；各有 Codex 對應版於 `../.codex/agents/` |
| `skills/` | 依需求載入的工作流；`baton-dispatch`、`provider-routing` 為自有，`headroom-protocol`、`speak-human-tw` symlink 至 `../.agents/skills/` |
| `settings.json` | Hooks、最小唯讀 allowlist、plugins 與介面設定；不指定主模型、effort 或 fallback |
| `examples/headroom-mcp.merge.json` | 可攜的 MCP 宣告片段；手動 merge 進本機 `mcp_servers.json`（後者含機器路徑，不入庫） |
| `hooks/`, `scripts/`, `sh/` | 監控、用量診斷、執行版本防護與 statusline |
| `plans/orchestration-plan.md` | 現況、待觀察事項與精簡決策紀錄 |
| `prompts/` | Claude App 與 Cowork 可直接貼用的配置 |
| `tests/` | 不需額外相依套件的契約與機制測試 |

`projects/`、`telemetry/`、`plugins/`、快取、憑證與使用中的 `$HOME/.claude.json` 都是本機執行狀態，不屬於可攜契約。跨 agent 共用知識（如 Headroom runtime）在 `../.agents/`。

## 路由

主模型與 effort 由使用者選擇；H／X 是建議組合，不會自動切換。跨 provider dispatch、
fallback、role routing 與 verifier 觸發條件全部收斂在 `skills/provider-routing/`，
按需載入——本 README 不再重述，避免雙 source of truth。

## 初始設定

1. `plan-verifier` 與 `security-reviewer` 需要 Claude Code 2.1.207 以上版本。
2. 新機器僅在 `$HOME/.claude` 不存在時直接套用；若已存在，先備份再合併（`sync.sh` 自動備份），不得取代憑證或本機狀態。
3. Headroom 生命週期與升級流程見 `../.agents/docs/headroom-runtime.md`；base URL 為 machine-local，不得寫進 tracked `settings.json`。
4. `rtk` 需另行安裝（macOS：`brew install rtk`）；未安裝時 hook 採 fail-open。
5. 修改 settings／agents／skills／prompts 後，開新 session 才能可靠載入。

## 驗證

```bash
python3 -m unittest discover -s tests -v
scripts/usage-report --days 7
jq empty settings.json examples/headroom-mcp.merge.json
sh -n sh/statusline.sh && git diff --check
```

Codex／ChatGPT 跨機器部署流程見 `../.codex/DEPLOY.md`。
