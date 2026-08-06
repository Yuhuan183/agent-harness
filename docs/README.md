# 文件導覽

本目錄保存 agent-harness 的方法論, 研究依據, 部署操作與歷史決策; 這些文件不會部署到
`~/.claude`, `~/.codex` 或 `~/.agents`. 專案全貌與架構圖先看[根 README](../README.md).

## 依目的閱讀

| 你要做什麼 | 從哪裡開始 | 接著看 |
|---|---|---|
| 由上而下讀懂整套架構 | [架構總覽](architecture.md) | [根 README](../README.md) |
| 理解整體架構與資料流 | [根 README](../README.md) | [Harness Engineering Playbook](harness-engineering.md) |
| 安裝, 同步或回滾 | [配置與部署](setup.md) | [Claude README](../main/claude/README.md), [Codex README](../main/codex/README.md) |
| 修改 leaf role 或派工契約 | [Playbook: Leaf 分派](harness-engineering.md#leaf-分派的三層契約) | [Briefs](../main/claude/skills/baton-dispatch/references/briefs-and-stops.md) |
| 評估 model/effort/provider | [研究摘要](research/README.md) | [Claude routing](../main/claude/model-routing.toml), [Codex routing](../main/codex/model-routing.toml) |
| 用 Fable 5 時避免被切到 Opus | [Fable 5 安全 fallback](fable-5-fallback.md) | [provider-routing](../main/claude/skills/provider-routing/SKILL.md) |
| 查 experience-ledger 指標 | [Metrics](../main/.agents/skills/experience-ledger/references/metrics.md) | [skill 本體](../main/.agents/skills/experience-ledger/SKILL.md) |
| 驗證派工狀態與路由證據 | [派工生命週期](dispatch-lifecycle.md) | [bridge-liveness](../main/claude/skills/provider-routing/references/bridge-liveness.md) |
| 診斷 context 或工具輸出 | [Headroom runtime](../main/.agents/docs/headroom-runtime.md) | [RTK](../main/claude/RTK.md) |
| 審視文檔與開發指引是否對齊 | [2026-07-28 統一稽核](document-audit-2026-07-28.md) | [可重跑 inventory](document-inventory.json) |
| 理解 QC 怎麼把關 | [QC 白話說明](qc-explainer.md) | [baton-dispatch](../main/claude/skills/baton-dispatch/SKILL.md) |
| 理解 hook 系統怎麼運作 | [Hook 系統](hook-system.md) | [settings.json](../main/claude/settings.json) |
| 跑行為 trap eval | [evals/traps/](../evals/traps/) 各 README | [QC 說明](qc-explainer.md) 取證段 |
| 深度審查本 repo 設計 | [harness-review](../.agents/skills/harness-review/SKILL.md) (dev-only) | [plan](../main/claude/plans/orchestration-plan.md) |
| 決定下一步做什麼 | [待辦方向](research/README.md#待辦方向) | [plan](../main/claude/plans/orchestration-plan.md) |

## 文件責任

| 文件 | 保存內容 | 不保存內容 |
|---|---|---|
| [架構總覽](architecture.md) | 由上而下的骨幹敘事: 架構圖, 核心想法, QC, 生命週期, hook, 附檔導引 | 各層細節 (指向專門文檔), 可變的 model 數值 |
| [Harness Engineering Playbook](harness-engineering.md) | 可跨專案複用的設計與驗證方法 | 當前 route pins, 實驗原始數據 |
| [研究摘要](research/README.md) | benchmark 快照, 成本口徑, 案例取捨, 研究缺口 | runtime 強制規則, 現行 route pins |
| [配置與部署](setup.md) | bootstrap, apply, 驗收與回滾步驟 | 模型選擇理由 |
| [契約瘦身規範](contract-slimming.md) | CLAUDE.md/AGENTS.md 的內容判定, 預算原則與驗收 | 歷史歷程, 當前 orchestration 狀態 |
| [派工生命週期](dispatch-lifecycle.md) | 派工五個狀態的承載物, 不成立的推論, 驗證清單 | 派工形狀與 QC (baton-dispatch), provider 選擇 (provider-routing) |
| [Hook 系統](hook-system.md) | fail-open/fail-closed 語意, 逐事件清單, 為何值得信任 | hook 內部實作細節 (各 hook 檔內 docstring) |
| [Orchestration plan](../main/claude/plans/orchestration-plan.md)+[history](../main/claude/plans/orchestration-history.md) | 當前最新方案; append-only 決策歷程 | 完整方法論與研究全文 |

## Runtime 真相源

實際執行行為不由本目錄決定:

- Claude main contract: [`main/claude/CLAUDE.contract.md`](../main/claude/CLAUDE.contract.md)
- Codex main contract: [`main/codex/AGENTS.contract.md`](../main/codex/AGENTS.contract.md)
- Claude leaf roles: [`main/claude/agents/`](../main/claude/agents/)
- Codex leaf roles: [`main/codex/agents/`](../main/codex/agents/)
- 共用 skills: [`main/.agents/skills/`](../main/.agents/skills/)
- 部署映射: [`scripts/deployment-manifest.tsv`](../scripts/deployment-manifest.tsv)

## 維護規則

1. 同一規則只保留一個真相源; 其他文件用連結與短摘要指過去.
2. README 說明全貌與入口, 不承載會頻繁變動的 model 數值或完整操作細節.
3. benchmark, effort, 日期與成本口徑只放研究摘要或 routing data, 不寫成永久能力宣稱.
4. 已落地的 runtime 規則從 plan 移出; 歷史判斷留在 Git 或明確標示的決策紀錄.
5. 文件改動仍需通過 contract tests, 連結檢查, `git diff --check` 與部署 dry-run.
6. 語言分層: runtime 檔案 (contracts, roles, skills, script 註解) 的**操作本體** (指令, 流程, 格式) 用英文, 人讀文件用 zh-TW. 窄例外: skill/agent `description` 的**觸發詞**與對使用者輸出的**模板**可用所需語言以對上使用者; `speak-human-tw` 是繁中素材. 其餘 runtime 中文即漂移.
7. 標點: 人讀文件寫 zh-TW 文字 + 英文術語 + 半形標點 (`, . : ; ? ! ( ) " ' -`), 標點後空一格, 本條自身即範例. 全形只留在五處:

   - 逐字引用的外部原文.
   - `speak-human-tw` 繁中素材.
   - `evals/traps/**` 的 fixture 與結果表 (文字本身是被量的變數).
   - skill `description` 的觸發詞與對使用者輸出的模板. 前者被 s10 trap 以位元組釘住, 後者是給人看的成品.
   - 程式裡拿全形當資料比對的字面值 (regex class, 對前四類的逐字斷言).

   引號 (「」『』《》〈〉) 與破折號沒有半形對應, 照舊. 全樹已於 2026-08-04 掃過一次, 新文字直接用半形寫; `docs/**` 這層由測試盯住.
8. 讀者分層與呈現. 全域底線是短句: 一句一義, 拆掉嵌套修飾, 但術語照留 - 換成白話近義詞會把精確性一起換掉. 在此之上分三層, 依讀者分而不依主題分:

   | 層 | 涵蓋 | 寫法 |
   |---|---|---|
   | 給模型讀 | contracts, roles, skills, script 註解的操作本體 | 英文, 見規則 6 |
   | 說明與研究 | [架構總覽](architecture.md), [QC 白話說明](qc-explainer.md), [research/](research/) | 讀者不必先懂本 repo 的內部詞彙. 核心概念先給圖, 數據對比先給表, 結論條列; 散文只用來講圖表講不了的因果 |
   | 操作與規範 | [setup](setup.md), [hook-system](hook-system.md), [dispatch-lifecycle](dispatch-lifecycle.md), [contract-slimming](contract-slimming.md), 兩份 README | 直白精簡, 不為了淺顯加篇幅 |

   字數棘輪目前只蓋住八份文件, 而未受管的 `research/` 一層就比受管全部還大 - 發散來自沒被量過, 不是來自寫作習慣. 說明與研究層的棘輪在改寫落地後才依實測值訂, 先訂會把改寫卡在舊形狀裡.
