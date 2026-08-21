# 文件導覽

本目錄保存 agent-harness 的方法論, 研究依據, 部署操作與歷史決策; 這些文件不會部署到
`~/.claude`, `~/.codex` 或 `~/.agents`. 專案全貌與架構圖先看[根 README](../README.md).

## 依目的閱讀

| 你要做什麼 | 從哪裡開始 | 接著看 |
|---|---|---|
| 由上而下讀懂整套架構 | [架構總覽](architecture/architecture.md) | [根 README](../README.md) |
| 從最小單位往上看懂 agent engineering | [分層剖析](architecture/architecture.md) | [架構總覽](architecture/architecture.md), [Playbook](engineering-playbook.md) |
| 評估一個升級提案 | [升級評估: 五個問題](architecture/architecture.md#六-升級評估-五個問題) | [跨層的兩條軸](architecture/architecture.md#四-跨層的兩條軸), [evidence-ladder](../main/.agents/skills/evidence-ladder/SKILL.md) |
| 理解整體架構與資料流 | [根 README](../README.md) | [Harness Engineering Playbook](engineering-playbook.md) |
| 安裝, 同步或回滾 | [配置與部署](setup.md) | [Claude README](../main/claude/README.md), [Codex README](../main/codex/README.md) |
| 修改 leaf role 或派工契約 | [Playbook: Leaf 分派](engineering-playbook.md#leaf-分派的三層契約) | [Briefs](../main/claude/skills/baton-dispatch/references/briefs-and-stops.md) |
| 評估 model/effort/provider | [研究摘要](research/README.md) | [Claude routing](../main/claude/model-routing.toml), [Codex routing](../main/codex/model-routing.toml) |
| 評估 Matt Pocock 工程 skills 的導入方式 | [導入研究](research/mattpocock-skills-integration.md) | [蒸餾實作計畫](plans/engineering-workflow-distillation.md) |
| 用 Fable 5 時避免被切到 Opus | [Fable 5 安全 fallback](research/fable-5-fallback.md) | [provider-routing](../main/claude/skills/provider-routing/SKILL.md) |
| 查 experience-ledger 指標 | [Metrics](../main/.agents/skills/experience-ledger/references/metrics.md) | [skill 本體](../main/.agents/skills/experience-ledger/SKILL.md) |
| 驗證派工狀態與路由證據 | [派工生命週期](dispatch-lifecycle.md) | [bridge-liveness](../main/claude/skills/provider-routing/references/bridge-liveness.md) |
| 診斷 context 或工具輸出 | [Headroom runtime](../main/.agents/docs/headroom-runtime.md) | [RTK](../main/claude/RTK.md) |
| 審視文檔與開發指引是否對齊 | [2026-07-28 統一稽核](document-audit.md) | [可重跑 inventory](document-inventory.json) |
| 理解 QC 怎麼把關 | [QC 白話說明](qc-explainer.md) | [baton-dispatch](../main/claude/skills/baton-dispatch/SKILL.md) |
| 理解 hook 系統怎麼運作 | [Hook 系統](hook-system.md) | [settings.json](../main/claude/settings.json) |
| 跑行為 trap eval | [evals/traps/](../evals/traps/) 各 README | [QC 說明](qc-explainer.md) 取證段 |
| 跑多回合 lifecycle replay | [evals/replay/](../evals/replay/) | [存活判準](research/lifecycle-replay.md) |
| 深度審查本 repo 設計 | [harness-review](../.agents/skills/harness-review/SKILL.md) (dev-only) | [orchestration 不變量](plans/orchestration-state.md) |
| 重查上游或蒸餾一個新的 | [upstream-distillation](../.agents/skills/upstream-distillation/SKILL.md) (dev-only) | [peer-harnesses](research/peer-harnesses.md) |
| 決定下一步做什麼 | [待辦方向](research/README.md#待辦方向) | [orchestration 不變量](plans/orchestration-state.md) |

## 文件責任

每份文件對應[四層](architecture/architecture.md#三-四層地圖)的哪一層寫在第一欄. 有四件橫跨所有
層, 標成「跨層」: 證據 (憑什麼算數), 部署 (規則怎麼真的到機器上), 授權 (誰有權決定)
與成本 (值不值得). 有兩層的規範不在
`docs/` 底下 —— ② Context 與 ③ Loop 由出貨的 skill 擁有, 那欄直接指過去.

| 層 | 文件 | 保存內容 | 不保存內容 |
|---|---|---|---|
| 跨層 · 地圖 | [架構總覽](architecture/architecture.md) | 完整資料流, 核心想法, 四層地圖, 跨層的兩條軸與四件橫跨的事, 升級評估的五個問題 | 每一層自己的職責與實作 (在四份層文件), 跨專案方法論 (在 playbook), 會過期的量測值 (指向腳本) |
| Context | [context-engineering](architecture/context-engineering.md) | 模型看到什麼: 一條子句怎麼寫, 一個 window 裡放什麼 | 預算的判定表與驗收 (在契約瘦身) |
| Harness | [harness-engineering](architecture/harness-engineering.md) | 模型周圍: 工具, 權限, 監控, 防護欄 | 每道 hook 的攔截條件 (在 hook 系統) |
| Loop | [loop-engineering](architecture/loop-engineering.md) | 單一 agent 的迴路: 規劃 → 執行 → 驗證 → 重試, 各自的停止條件 | 派工形狀與 brief (在 baton-dispatch) |
| Graph | [graph-engineering](architecture/graph-engineering.md) | 多 agent 協作: 誰先做, 誰並行, 做完給誰; QC 與五個狀態 | QC 規則字面 (在派工 skill), 狀態承載物 (在派工生命週期) |
| 跨層 · 全六層 | [分層剖析](architecture/architecture.md) | 六層各自的職責, 實作, 儀器, 已知失效與升級判準; 跨層的兩條軸; 升級評估的五個問題 | 跨專案通則的完整論證 (在 playbook), 這個系統的骨幹敘事 (在架構總覽), 實驗原始數據 (在 research/) |
| 跨層 · 通則 | [Harness Engineering Playbook](engineering-playbook.md) | 可跨專案複用的設計與驗證方法, 以及每條通則的完整論證 | 當前 route pins, 實驗原始數據, 本 repo 逐層的實作 (在分層剖析) |
| ① 子句 | [契約瘦身規範](contract-slimming.md) | CLAUDE.md/AGENTS.md 的內容判定, 預算原則與驗收 | 歷史歷程, 當前 orchestration 狀態 |
| ② Context | 規範在 [contract-slimming](contract-slimming.md) 與 [headroom-runtime](../main/.agents/docs/headroom-runtime.md) | — | — |
| ③ Loop | 規範在 [baton-dispatch](../main/claude/skills/baton-dispatch/SKILL.md) | — | — |
| ④ Harness | [Hook 系統](hook-system.md) | fail-open/fail-closed 語意, 逐事件清單, 為何值得信任 | hook 內部實作細節 (各 hook 檔內 docstring) |
| ⑤ Graph | [QC 白話說明](qc-explainer.md) | 為什麼需要 QC, 四個步驟各吃什麼, 白話的取證說明 | 有約束力的 QC 規則字面 (在兩份派工 skill) |
| ⑤ Graph | [派工生命週期](dispatch-lifecycle.md) | 派工五個狀態的承載物, 不成立的推論, 驗證清單 | 派工形狀與 QC (baton-dispatch), provider 選擇 (provider-routing) |
| ⑤ Graph | [Fable 5 安全 fallback](research/fable-5-fallback.md) | 用 Fable 5 時怎麼避免被切到 Opus, 以及可行性邊界 | 本 repo 的跨 provider fallback 規則 (在 provider-routing) |
| ⑥ Evidence | [研究摘要](research/README.md) | benchmark 快照, 成本口徑, 案例取捨, 研究缺口; `research/` 底下唯一的現行結論來源 | runtime 強制規則, 現行 route pins, 逐次查核的原始紀錄 (在 [landing-log](research/landing-log.md)) |
| ⑥ Evidence | [Matt Pocock skills 導入研究](research/mattpocock-skills-integration.md) | 上游快照, 工作流比較, 相容性, 採用與拒絕理由 | 實作進度, runtime skill 本體 |
| ⑥ Evidence | [2026-07-28 統一稽核](document-audit.md) | 那一次稽核的六維度結果與範圍信封 | 之後的變更 (信封是活的, 見該文件的注記) |
| 跨層 · 部署 | [配置與部署](setup.md) | bootstrap, apply, 驗收與回滾步驟 | 模型選擇理由 |
| 跨層 · 計畫 | [Engineering workflow 蒸餾實作計畫](plans/engineering-workflow-distillation.md) | 已核准方向, 分階段 scope, gates, rollback 與 completion criteria | 上游研究全文, 已部署狀態 |
| 跨層 · 清單 | [Orchestration 不變量](plans/orchestration-state.md) | 八條必須成立的性質, 各自指向擁有者; 改動前後逐條檢查用 | 每條的論證與實作 (在四份層文件) |
| 跨層 · 紀錄 | [Orchestration 決策歷程](plans/orchestration-history.md) | append-only, 依時間序; 保留原始措辭 | 當前狀態 (在不變量表) |

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
4. 已落地的 runtime 規則從 plan 移出; 歷史判斷留在 Git 或明確標示的決策紀錄. `docs/research/` 底下**只有 [`research/README.md`](research/README.md) 是現行指引**, 其餘是紀錄: 它們刻意保留被後來證據推翻的段落, 所以不進「指引是否還對」的稽核範圍. 分界寫在 [`document-inventory.json`](document-inventory.json), 由 `test_document_inventory.py` 盯住, 由 [`scripts/docs-size-report.py`](../scripts/docs-size-report.py) 分層回報.
5. 文件改動仍需通過 contract tests, 連結檢查, `git diff --check` 與部署 dry-run.
6. 語言分層: runtime 檔案 (contracts, roles, skills, script 註解) 的**操作本體** (指令, 流程, 格式) 用英文, 人讀文件用 zh-TW. 窄例外: skill/agent `description` 的**觸發詞**與對使用者輸出的**模板**可用所需語言以對上使用者; `readable-zh-tw` 是繁中素材. 其餘 runtime 中文即漂移.
7. 標點: 人讀文件寫 zh-TW 文字 + 英文術語 + 半形標點 (`, . : ; ? ! ( ) " ' -`), 標點後空一格, 本條自身即範例. 全形只留在五處:

   - 逐字引用的外部原文.
   - `readable-zh-tw` 繁中素材.
   - `evals/traps/**` 與 `evals/replay/**` 的 fixture, 情境與結果表 (文字本身是被量的變數).
   - skill `description` 的觸發詞與對使用者輸出的模板. 前者被 s10 trap 以位元組釘住, 後者是給人看的成品.
   - 程式裡拿全形當資料比對的字面值 (regex class, 對前四類的逐字斷言).

   引號 (「」『』《》〈〉) 與破折號沒有半形對應, 照舊. 全樹已於 2026-08-04 掃過一次, 新文字直接用半形寫; `docs/**` 這層由測試盯住.
8. 讀者分層與呈現. 全域底線是短句: 一句一義, 拆掉嵌套修飾, 但術語照留 - 換成白話近義詞會把精確性一起換掉. 在此之上分三層, 依讀者分而不依主題分:

   | 層 | 涵蓋 | 寫法 |
   |---|---|---|
   | 給模型讀 | contracts, roles, skills, script 註解的操作本體 | 英文, 見規則 6 |
   | 說明與研究 | [架構總覽](architecture/architecture.md), [context](architecture/context-engineering.md), [harness](architecture/harness-engineering.md), [loop](architecture/loop-engineering.md), [graph](architecture/graph-engineering.md), [QC 白話說明](qc-explainer.md), [研究總結](research/README.md) | 讀者不必先懂本 repo 的內部詞彙. 核心概念先給圖, 數據對比先給表, 結論條列; 散文只用來講圖表講不了的因果. 術語照留 —— 換白話近義詞會把精確性一起換掉 —— 但**內部代號** (`s11`, `p1b` 這類 trap 與 replay 情境編號) 第一次出現時, 同一句裡要有東西說它問的是什麼. 研究日誌不在這一層: 它們寫給跑過那批實驗的人看 |
   | 操作與規範 | [setup](setup.md), [hook-system](hook-system.md), [dispatch-lifecycle](dispatch-lifecycle.md), [contract-slimming](contract-slimming.md), 兩份 README | 直白精簡, 不為了淺顯加篇幅 |

   **`docs/**` 沒有字數預算** (2026-08-08 起). 字數上限量的是 push 成本 — 每回合或每次派工都要付的位元組 — 而 manifest 部署的檔案裡沒有一份在 `docs/` 底下: 這一層是 pull 成本, 由打開它的人付一次, 而且可以不看完. 用擋 commit 的天花板管 pull 成本, 買到的是「記錄新學到的東西要先調預算」這種摩擦. 這一層改由兩件事看住: [`scripts/docs-size-report.py`](../scripts/docs-size-report.py) 只報不擋, 另有一道 `DOC_SPRAWL_CEILING` 數量級鬆閘, 只抓「一份文件已經不是一份文件」. 逼近鬆閘的正解是拆檔或搬回真正的 owner, 不是調高常數. 預算仍然嚴格生效在出貨層: 兩份契約, skill 與 role 的 `description`, 以及每一支出貨 skill 的本文, 規範見[契約瘦身](contract-slimming.md).

9. 證據錨點: **不要用裸的 short SHA 指涉本 repo 的變更**. 分支在 merge 前會 rebase, rebase 會改寫每一個 SHA, 所以那種引用在被整合的當下就死了 - 2026-08-08 掃描顯示本樹十個本地 SHA 引用死了六個, 而兩個正確的都是外部的, 都是完整長度, 都帶連結. 指外部 repo 就照那個形狀寫; 指本 repo 就改用**內容指紋**: trap 在 `surface.tsv` 宣告量測面, [`evals/scripts/trap-surface.py`](../evals/scripts/trap-surface.py) 算出 sha256, 結果列記 `[surface <short>]`. 指紋由位元組算出, rebase, 搬檔, 改名都不影響. 現況由 [`scripts/evidence-check.py`](../scripts/evidence-check.py) 只報不擋.
