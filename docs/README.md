# 文件導覽

本目錄保存 agent-harness 的方法論、研究依據、部署操作與歷史決策；這些文件不會部署到
`~/.claude`、`~/.codex` 或 `~/.agents`。專案全貌與架構圖先看[根 README](../README.md)。

## 依目的閱讀

| 你要做什麼 | 從哪裡開始 | 接著看 |
|---|---|---|
| 理解整體架構與資料流 | [根 README](../README.md) | [Harness Engineering Playbook](harness-engineering.md) |
| 安裝、同步或回滾 | [配置與部署](setup.md) | [Claude README](../.claude/README.md)、[Codex README](../.codex/README.md) |
| 修改 leaf role 或派工契約 | [Playbook：Leaf 分派](harness-engineering.md#leaf-分派的三層契約) | [Briefs and Stops](../.claude/skills/baton-dispatch/references/briefs-and-stops.md) |
| 評估 model／effort／provider | [研究摘要](harness-engineering-research.md) | [Claude routing](../.claude/model-routing.toml)、[Codex routing](../.codex/model-routing.toml) |
| 查 experience-ledger 指標 | [Metrics](../.agents/skills/experience-ledger/references/metrics.md) | [Experience Ledger skill](../.agents/skills/experience-ledger/SKILL.md) |
| 診斷 context 或工具輸出 | [Headroom runtime](../.agents/docs/headroom-runtime.md) | [RTK](../.claude/RTK.md) |
| 理解目前決策與下一步 | [Orchestration plan](../.claude/plans/orchestration-plan.md) | [研究摘要：仍待驗證](harness-engineering-research.md#仍待本機驗證) |

## 文件責任

| 文件 | 保存內容 | 不保存內容 |
|---|---|---|
| [Harness Engineering Playbook](harness-engineering.md) | 可跨專案複用的設計與驗證方法 | 當前 route pins、實驗原始數據 |
| [研究摘要](harness-engineering-research.md) | benchmark 快照、成本口徑、案例取捨、研究缺口 | runtime 強制規則、現行 route pins |
| [配置與部署](setup.md) | bootstrap、apply、驗收與回滾步驟 | 模型選擇理由 |
| [CLAUDE.md 瘦身紀錄](global-claude-md-slimming.md) | 歷史決策與逐區塊驗收 | 當前 orchestration 狀態 |
| [Orchestration plan](../.claude/plans/orchestration-plan.md) | 短期現況、未決項與決策紀錄 | 完整方法論與研究全文 |

## Runtime 真相源

實際執行行為不由本目錄決定：

- Claude main contract：[`.claude/CLAUDE.contract.md`](../.claude/CLAUDE.contract.md)
- Codex main contract：[`.codex/AGENTS.contract.md`](../.codex/AGENTS.contract.md)
- Claude leaf roles：[`.claude/agents/`](../.claude/agents/)
- Codex leaf roles：[`.codex/agents/`](../.codex/agents/)
- 共用 skills：[`.agents/skills/`](../.agents/skills/)
- 部署映射：[`scripts/deployment-manifest.tsv`](../scripts/deployment-manifest.tsv)

## 維護規則

1. 同一規則只保留一個真相源；其他文件用連結與短摘要指過去。
2. README 說明全貌與入口，不承載會頻繁變動的 model 數值或完整操作細節。
3. benchmark、effort、日期與成本口徑只放研究摘要或 routing data，不寫成永久能力宣稱。
4. 已落地的 runtime 規則從 plan 移出；歷史判斷留在 Git 或明確標示的決策紀錄。
5. 文件改動仍需通過 contract tests、連結檢查、`git diff --check` 與部署 dry-run。
