# `.claude/` — Claude Code Harness 契約

> 專案全貌與跨平台資料流見[根 README](../../README.md); 方法, 研究與部署指引見
> [docs/README.md](../../docs/README.md).

可跨機器共用的 Claude Code/Cowork 配置, 回寫到 `~/.claude/`. Git 僅保存規則與可攜機制;
憑證, 對話紀錄, 遙測, 快取, MCP 執行狀態與機器路徑皆留在本機.
套用到全域: 專案根 `scripts/sync.sh`.

## 內容索引

| 路徑 | 職責 |
|---|---|
| `CLAUDE.contract.md` | Claude Code 執行契約源檔 (部署為 `~/.claude/CLAUDE.md`; 改名避免本 repo 內 session 重複載入); 僅主 agent 使用的精簡協調規則 (~600 tokens) |
| `agents/` | 七個自足的 Claude leaf roles; model 與 effort 由 active deployment preset 的 frontmatter pins 決定; 各有 Codex 對應版於 `../.codex/agents/` |
| `skills/` | 依需求載入的工作流源檔 (部署為 `~/.claude/skills/<name>`; 改名理由同 `CLAUDE.contract.md` — Claude Code 會掃巢狀 `.claude/skills/`, 同名時本 repo 內會列兩份, 載兩次); `baton-dispatch`, `provider-routing` 為自有; `speak-human-tw`, `experience-ledger`, `evidence-debugging`, `test-first-change`, `evidence-ladder` 整個目錄 symlink 至 `../.agents/skills/`; `headroom-protocol` 與 `task-observer` 是本端薄目錄 (自有 `SKILL.md` 帶 `disable-model-invocation: false`, 共用本體以 `shared-instructions.md` symlink 引用), 因為共用 body 帶不了那一行; `task-observer` 可在 skill 使用受挫後主動詢問是否記錄改善觀察; `evidence-debugging` 與 `test-first-change` 蒸餾自上游, 見各自 `ATTRIBUTION.md`; `evidence-ladder` 為本 repo 自撰, 因此沒有 |
| `settings.json` | Hooks, 最小唯讀 allowlist, codex plugin (唯一強依賴) 與介面設定; 不指定主模型, effort 或 fallback. 其他 plugin 屬本機自理, enable 寫 `settings.local.json` (不入庫, sync 不覆蓋) |
| `examples/headroom-mcp.legacy.json` | 舊版 MCP 宣告範例, 僅供不支援 Headroom installer 的環境參考; 一般安裝使用 `headroom mcp install --agent claude --proxy-url http://127.0.0.1:8787` |
| `hooks/`, `scripts/`, `sh/` | 監控, 用量診斷, 路由檢核 (`scripts/model-routing`), 執行版本防護, 紅測試 commit 閘 (`hooks/commit-test-gate.py` 配 `githooks/pre-commit`, 逃生口 `AGENT_SKIP_TEST_GATE=1`; `--no-verify`/`-c core.hooksPath=…` 這類自行停用 hook 的殘餘留給 CI) 與 statusline |
| `plans/orchestration-plan.md` | 現況, 待觀察事項與精簡決策紀錄 |
| `prompts/` | Claude App 與 Cowork 可直接貼用的配置 |
| `tests/` | 不需額外相依套件的契約與機制測試 |

`projects/`, `telemetry/`, `plugins/`, 快取, 憑證與使用中的 `$HOME/.claude.json` 都是本機執行狀態, 不屬於可攜契約. 跨 agent 共用知識 (如 Headroom runtime) 在 `../.agents/`.

## 路由

主模型與 effort 由使用者選擇; H/X 是建議組合, 不會自動切換. 跨 provider dispatch,
fallback, role routing 與 verifier 觸發條件全部收斂在 `skills/provider-routing/`,
按需載入. Claude 三個 profile 是 session/deployment preset, 不是 per-dispatch override; 以
在 source checkout 用 `scripts/model-routing activate-profile --profile <name>` 一次更新全部
frontmatter pins, review 後透過根目錄 `scripts/sync.sh --apply` 部署, 再開新 session. 該工具另
提供 `validate`/`resolve`/`check-pins`/`check-aliases` (每週 integrity 會自動比對部署與
source 漂移, 並以 leaf transcript 的真實 model id 驗證 `opus` 這類別名指向哪個世代);
經 `codex:codex-rescue` 呼叫的 Codex twin 則必須先用
`${CODEX_HOME:-$HOME/.codex}/scripts/model-routing resolve --surface claude-bridge`
解析 per-dispatch profile, 不套用 Claude 的 frontmatter pin. 兩側各自的資料來源都只有一份.

## 初始設定

1. `plan-verifier`, `security-reviewer` 與 `verifier` 需要 Claude Code 2.1.207 以上版本.
2. 新機器僅在 `$HOME/.claude` 不存在時直接套用; 若已存在則合併而非取代, 不得取代憑證或本機狀態; 回滾靠 git 重新部署.
3. Headroom 生命週期與升級流程見 `../.agents/docs/headroom-runtime.md`; base URL 為 machine-local, 不得寫進 tracked `settings.json`.
4. `rtk` 需另行安裝 (macOS: `brew install rtk`); 未安裝時 hook 採 fail-open.
5. 修改 settings/agents/skills/prompts 後, 開新 session 才能可靠載入.

## 驗證

```bash
main/.agents/scripts/python3-run -m unittest discover -s main/claude/tests -v
scripts/usage-report --days 7
scripts/usage-report --days 7 --by-session --top 20
jq empty settings.json examples/headroom-mcp.legacy.json
sh -n sh/statusline.sh && git diff --check
```

Codex/ChatGPT 跨機器部署流程見 `../.codex/DEPLOY.md`.
