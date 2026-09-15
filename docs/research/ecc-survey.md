# ECC (Everything Claude Code) 勘查

> 勘查日: 2026-09-08. 對象 [affaan-m/ecc](https://github.com/affaan-m/ecc),
> pin `5064474d4d762dc9640234a41617cccb79185cec` (2026-09-07, `VERSION` 檔為 `2.2.1`), MIT.
> 類別**同業**: 勘查為主. **2026-09-08 起有一條真的蒸餾了** (B15 → 計畫 Q1), 但落地的是概念改造而不是上游原句, 一個位元組都沒有複製, 出處記在
> `test_deployment.HookEnvDocumentationTests` 的 docstring 裡 (點名 ECC, 檔名, 勘查日, MIT) ——
> 與 `eli5` 那次同樣的處置, 因此仍然沒有獨立的 ATTRIBUTION 檔.
> 逐條處置在下面的表, 落地排程獨立成 [ECC 升級計畫](#升級計畫-結案表與重開條件).

## 這份文件回答什麼

ECC 是目前公開規模最大的 Claude Code plugin: 68 個 agent, 286 個 skill, 94 個 command,
24 個 hook entry, 277 支測試, 12 個 harness 的安裝面. 它和本專案走相反的方向 —— 它要**覆蓋面**,
本專案要**可驗證的最小規則集**. 相反方向的專案值得看, 因為它會先撞上規模帶來的失敗, 而那些失敗
是本專案的規則想避開的東西.

四個一句話結論:

| # | 結論 | 憑什麼 |
|---|---|---|
| 1 | 最值得拿的一條是 **fact-forcing**: 不要問模型「你確定嗎」, 要它交出外部可查的事實 | 自評的答案恆為「是」; 要求列出 importer 會強迫它真的去 Grep, 而調查本身改變了輸出 |
| 2 | 第二條是 **拒絕訊息會退化**: 同一段攔截文字在 session 裡累積, 會拉高模型掉進重複迴圈的機率 | ECC #2142 為此把前三次以後的拒絕改成單行帶序號; 本機 `denials.jsonl` 量到 18 連擊 |
| 3 | 它的規模本身是本專案「單一生成清單」規則的反面證據 | 三份常駐檔各記一組資產數字, 三組都不一樣, 其中兩組是錯的 |
| 4 | 它的證據等級低於本專案, 所以**形狀可借, 數字一律不借** | 旗艦守衛的效果宣稱是 n=2 個任務的 1–10 主觀評分, 而那個數字寫在 skill description 裡, 模型讀得到 |

## ECC 是聚合者, 不是獨立觀察者

計票前先算血緣. ECC 的規則有相當比例是第三方的:

- `skills/gateguard/` 的 fact-forcing 來自 [zunoworks/gateguard](https://github.com/zunoworks/gateguard),
  只在 hook 原始碼的註解裡點名, skill 的 `origin:` 欄寫 `community`.
- `skills/santa-method/` 的雙審斂合來自 `Ronald Skelton - Founder, RapportScore.ai`.
- 286 個 skill 裡 42 個 `origin: community`, 8 個 `ECC direct-port adaptation`.

**所以「ECC 也這麼做」不等於一票.** 下表凡是借來的規則, 票記在原作者頭上; ECC 自己掙來的那幾條
(拒絕衰減 #2142, adapter 矩陣, hook dispatcher 合併, MCP 斷路器, skill 健康遙測, 迴圈門檻調參)
才算 ECC 的獨立觀察.

## 逐條處置

母體是**本輪實際讀過的表面**所承載的規則, 共 42 條 (A 契約 8, B 強制 15, C 學習 7, D 自審 3,
E 安全 5, F 結構 4). 不是 ECC 的全部規則 —— 沒有讀的列在[最後一節](#沒有查的).
處置分佈: 已落地 11 (B15, B4, B10, C7 於 2026-09-08 落地), 佐證 5, 待採用 2, 不採用 21 (B6, B12, B1, B2, E4 量過後轉入), 不適用 1, 缺口但不排 2 —— 合計 42, 與母體相符.
兩條標「已落地 + 佐證」的 (B5, B13) 計入已落地那一欄.

「待採用」是本輪的例外標記, 意思是**排進計畫但還沒落地**. 本 repo 的常規是採用與實作同一輪完成,
否則紀錄會說謊; 這次使用者要的是報告與計畫而不是落地, 所以用一個明確不同的字, 不讓它讀起來像已經做了.

### A 契約層

| # | ECC 的規則 | 處置 | 查了什麼 |
|---|---|---|---|
| A1 | 身分/規則/指令拆成 `SOUL.md` + `RULES.md` + `AGENTS.md` + `CLAUDE.md` 四份常駐檔, 合計 15,607 B | 不採用 | 四份 `wc -c`; 本專案 `CLAUDE.contract.md` 3,367 B, `AGENTS.contract.md` 4,374 B. 四份之間安全規則講了三次 |
| A2 | `CLAUDE.md` 內嵌 prompt-defense baseline 六條 (身分不變, 不洩密, 外部內容視為不可信…) | 不採用 | 佔該檔約四分之一; 沒有任何一條能被檢查失敗, 屬偏好而非規則 |
| A3 | 常駐檔以散文寫下可數資產清單 | **不採用 + 反面證據** | 見[三個反面觀察](#三個反面觀察) |
| A4 | 知識落點規則: 個人筆記進 memory, 團隊知識進專案既有文件, 不重複寫兩處, 沒有明顯位置就先問 | 已落地 | 本專案 memory 契約已分 user/feedback/project/reference, 並規定 repo 已記錄的不存 |
| A5 | `skills/` 是正典工作流面, `commands/` 只是相容 shim | 不適用 | 本專案沒有 command 表面 |
| A6 | 大型重構避開 context 最後 20%, 低敏感任務容忍更高使用率 | 不採用 | 沒有可觀察的閾值; 本專案以 `headroom-protocol` 與 `compact-reseed` 處理同一問題 |
| A7 | Agent-First: 未經使用者提示即主動派工, 獨立操作平行 launch | **不採用 (分歧)** | 見[兩個分歧](#兩個分歧) |
| A8 | 測試覆蓋率硬性 80%, TDD 強制 | 不採用 | 比率門檻對本 repo 的主要資產 (契約文字, manifest, skill) 定義不出來; `test-first-change` 管的是形狀 |

### B 強制層 (hook)

| # | ECC 的規則 | 處置 | 查了什麼 |
|---|---|---|---|
| B1 | 每檔第一次 Edit/Write 攔一次, 要求交出: 誰 import 它, 受影響的公開 API, 資料 schema, 使用者指令逐字引用 | **量過, 不採用** (計畫 Q3; 首次 Edit 已調查 59–93%, 未調查上界 6.9%, 而下限由 client 強制) | `scripts/hooks/gateguard-fact-force.js:1103-1133`. 本 repo grep 過 `main/claude/prompts`, `main/*/skills`, `engineering-playbook.md`, 無等價規則; memory 有「狀態要當場觀察」但沒有機制 |
| B2 | 破壞性 shell: 影響清單 + 一行回滾程序 + 逐字指令 | **量過, 不採用** (計畫 Q3b; 374 次命中裡 70% 是清理暫存, 0 次碰託管狀態) | 同檔 `destructiveBashMsg()`. 本專案只在 `git commit` / `git push` 兩點設閘 |
| B3 | 每 session 第一個 shell 指令要先說「請求是什麼」「這條指令驗證什麼」 | 不採用 | 對 main session 是純稅, 且「有沒有引用」無法機械判定 |
| B4 | 拒絕訊息衰減: 前 3 次發完整區塊, 之後單行且帶本 session 序號, 讓連續拒絕永不逐字相同 | **改造後採用, 已落地 2026-09-08** (計畫 Q2; 只做訊息全靜態的那支) | 同檔 934-975 行的註解寫明機轉 (近乎相同的攔截區塊累積會拉高退化重複的機率). 本機 `denial-report.py` 實測: `commit-test-gate` (Bash 側, git 側對應是 `githooks/pre-commit`) 最長 18 連擊, `managed-target-guard` 5 連擊 |
| B5 | 每則拒絕帶**窄逃生口** (路徑 glob 豁免, 或單支 hook 停用), 不是只給總開關 | 已落地 + 佐證 | `docs/hook-system.md` 的 gate 表每列都有逃生口欄 |
| B6 | 擋掉對 linter/formatter 設定檔的修改 (agent 常改設定讓檢查變綠) | **量過, 不採用** (計畫 Q7; 過去 200 個 commit 裡 16 次動上限, 16 次都帶理由) | `scripts/hooks/config-protection.js`. 本 repo 的等價不是 eslint, 是測試裡的上限表與預算數字 |
| B7 | 擋掉 `--no-verify` 與 `-c core.hooksPath=` | **不採用 (分歧)** | 見[兩個分歧](#兩個分歧) |
| B8 | hook profile (minimal/standard/strict) + 以穩定 hook ID 逐支停用 | 不採用 | 本專案以逐 gate 具名逃生口達成同一目的; profile 會多出一組要對帳的組合狀態 |
| B9 | 同一事件的多支 hook 併成一個 dispatcher process, 保留逐 hook 控制 | 佐證 | ECC 有 24 個 hook entry 才需要合併; 本專案 12 支, playbook 已要求秒級 |
| B10 | SessionStart 注入內容硬上限 (預設 8,000 字元) 與截斷標記 | **改造後採用, 已落地 2026-09-08** (計畫 Q4; 全域上限不加, 改綁唯一無界的那段列舉) | `scripts/hooks/session-start.js:39,197-208`. 本專案 `weekly-integrity` 在 SessionStart 注入 finding, 篇幅無上限 |
| B11 | MCP server 健康斷路器: 不健康就擋掉呼叫並讓模型改用非 MCP 工具, 帶重連與再探測 | 缺口, 不排 | `scripts/hooks/mcp-health-check.js`. 本專案的 circuit breaker 只涵蓋 reviewer 服務; MCP 面沒有事故資料, 沒有資料就不加閘 |
| B12 | `PostToolUseFailure[Skill]` → skill 健康遙測 | **量過, 不採用** (計畫 Q6; 144 次呼叫 1 次失敗, 而那一次是參數寫錯不是 skill 壞掉) | `hooks/hooks.json`. 本專案 `task-observer` 只在使用者同意時寫, Skill 硬失敗完全無痕 |
| B13 | 迴圈偵測門檻依實測誤報從 3 調到 5, 理由寫在常數旁 | 已落地 + 佐證 | `scripts/hooks/ecc-context-monitor.js:22-26`. 與本 repo「守衛要帶三個量測數」同一條 |
| B14 | 每支 hook 宣告 `async` 與 `timeout` | 已落地 | playbook 第 5 節已要求秒級 |
| B15 | hook 讀的每個環境開關都必須被文件涵蓋, 雙向檢查, 且掃描器對它看不懂的存取形式**直接失敗**而不是略過 | **改造後採用, 已落地 2026-09-08** (計畫 Q1) | `tests/ci/gateguard-env-documented.test.js`, 本輪讀到品質最高的一支. 本機量測見計畫 Q1 |

### C 學習層

| # | ECC 的規則 | 處置 | 查了什麼 |
|---|---|---|---|
| C1 | instinct 模型: 原子 (一觸發一動作), 信心 0.3–0.9, 領域標籤, 證據回溯 | 不採用 | `skills/continuous-learning-v2/SKILL.md`. 信心分數沒有校準來源, 是模型自評的另一種寫法 |
| C2 | 專案範圍與全域分開, 同一條在 2+ 專案出現才升為全域 | 佐證 | 本專案 memory 目錄本來就是專案範圍; 升級規則我方沒有, 也沒有多專案語料可證 |
| C3 | 觀察落在 PreToolUse/PostToolUse 而非 Stop, 理由是可靠度 | 佐證 | 本專案 `delegation-audit` 與 `experience-pending` 落在 SubagentStart/Stop, 同一理由 |
| C4 | 背景觀察者用便宜模型, 有最小觀察數門檻, **預設關閉** | 佐證 | `config.json` 的 `observer.enabled: false`; 與本專案 `task-observer` 要明示同意才寫同向 |
| C5 | `/evolve`: 依觸發形狀把 instinct 叢集成 command / skill / agent | 不採用 | 本專案的 skill 是蒸餾產物, 不是生成物 |
| C6 | 觀察資料放在 `~/.claude` 之外, 因為 client 的敏感路徑守衛會擋掉背景寫入 | 佐證 (供應商製品) | 這是 ECC 觀察到的 client 行為, 本機 `~/.claude/telemetry` 未遇阻; 記下來, 遇到再說 |
| C7 | 平台不支援誠實宣告: Windows 上背景觀察者實際是 no-op (附 issue #2489), 連續失敗 N 次後寫警告 | **改造後採用, 已落地 2026-09-08** (計畫 Q8b; 維度從平台換成 payload 形狀) | 本專案 `hook-system.md` 有「這套設計的邊界」節, 但沒有「此機制在此平台等於沒有」這種逐機制宣告位 |

### D 自審層

| # | ECC 的規則 | 處置 | 查了什麼 |
|---|---|---|---|
| D1 | `skills-health`: 逐 skill 成功率, 下滑偵測, 待決修訂, 版本 | 缺口, 不排 | `scripts/lib/skill-evolution/health.js`. 本專案 `experience-ledger` 有 role×provider 指標, 沒有 per-skill; 語料量不足以支撐 |
| D2 | `harness-audit`: 帶 `RUBRIC_VERSION` 的分類評分, 依偵測到的 provider 條件計分 | 不採用 | 打分會製造「分數上升即改善」的假訊號; 本專案 `harness-review` 是證據優先, 不打分 |
| D3 | `harness-adapter-compliance`: 逐 harness 能力矩陣, 每列必填 state / 不支援面 / 安裝路徑 / **驗證指令** / 風險 / `last_verified_at` / owner / 來源文件, 產生到文件的標記區塊之間 | **待採用 (改造)** → 計畫 Q5 | `scripts/lib/harness-adapter-compliance.js`. 12 列, state 四級. 注意它自己壞了: 見[三個反面觀察](#三個反面觀察) |

### E 安全層

| # | ECC 的規則 | 處置 | 查了什麼 |
|---|---|---|---|
| E1 | least agency: 模型不得是 shell / 網路出口 / repo 外寫入 / 密鑰讀取 / workflow dispatch 的最終權威 | 已落地 | `the-security-guide.md:257-283`. 本專案: no-write role 無 Bash 表面, `push-consent-gate`, `managed-target-guard` |
| E2 | 可觀測性最小欄位集: tool, input 摘要, 動到的檔, 核准決策, 網路嘗試, session/task id | 已落地 (缺一欄) | 本專案 `denials.jsonl` 與 `delegation.jsonl` 覆蓋除「網路嘗試」外的全部; 不記指令內容是刻意的 |
| E3 | kill switch 殺 process group 而非父程序; 無人看管迴圈加心跳, 逾時自動殺 | 不採用 | 本專案沒有無人看管迴圈, `Workflow` 需使用者明示 opt-in |
| E4 | 記憶是持久化攻擊面: 不放密鑰, 專案與全域分離, **不可信任務後輪替**, 高風險工作流關閉長期記憶 | **量過, 毯子版不採用** (計畫 Q8; 88% 的 memory 寫入都在抓過外部內容的 session 裡); 殘餘是一句寫作紀律, 決定權在使用者 | 同檔 339-352 行. 本專案 memory 只增不汰, 沒有輪替規則 |
| E5 | 治理事件捕捉 (secrets, policy violation, approval request) 另開一條 hook | 不採用 | 與 `denial_log` 重疊; 本專案刻意不記內容 |

### F 結構層

| # | ECC 的規則 | 處置 | 查了什麼 |
|---|---|---|---|
| F1 | 每個 skill frontmatter 帶 `origin:` 出處欄 | **待採用 (改造, 09-08 重新定範圍)** → 計畫 Q10 | 覆蓋率 286/286; 本專案 ATTRIBUTION 帶 pin 比它強, 但去重後 12 支 skill 只有 5 支有 |
| F2 | 模組化安裝 profile (minimal / core / developer / opencode), 以模組為單位決定裝什麼 | 不採用 | 會讓「這台機器裝了什麼」變成要對帳的狀態; 本專案單一 manifest 40 列全裝 |
| F3 | 文件多語系鏡像 | **不採用 + 反面證據** | 見[三個反面觀察](#三個反面觀察) |
| F4 | skill 放置政策: 策展的進 repo, 生成或匯入的進 `~/.claude/skills` | 已落地 | `deployment-manifest.tsv` 決定哪些進 HOME |

## 三個反面觀察

規模帶來的失敗, 三個都是本專案現行規則的直接證據.

**同一個可數事實寫在三個地方, 三個都不一樣.** 實際樹上是 68 agent / 286 skill / 94 command
(`ls agents/*.md`, `ls -d skills/*/SKILL.md`, `ls commands/*.md`). 而:

| 檔案 | 它說的 | 差距 |
|---|---|---|
| `AGENTS.md:3` | 68 / 286 / 94 | 正確 |
| `SOUL.md:4` | 30 / 135 / 60 | 少一半以上 |
| `WORKING-CONTEXT.md` (標題是 Current Truth) | 47 agent / 181 skill / 79 command, 版本 `v1.10.0` | 停在 2026-04-08; `VERSION` 檔是 `2.2.1` |

三份都在 prompt 表面上, 模型讀得到. 本專案的 `document-inventory.json` 加 census 就是為了讓
同一事實只有一個生成來源; 這是那條規則至今最清楚的一次外部佐證.

**產生器有欄位, 沒有讓欄位過期的檢查.** `harness-adapter-compliance.js` 要求每列都有
`last_verified_at`, 而現存的值是 `2026-05-12`, `2026-05-17`, `2026-08-10` —— 最舊的離 HEAD
四個月. 全 repo `grep last_verified_at` 只有兩個檔命中: 產生器自己與它產生的文件, 沒有任何測試.
**教訓不是「別加這個欄位」, 是「加欄位的同時要加讓它過期的測試」** —— 這條寫進計畫 Q5.

**多語系鏡像會吃掉文件目錄.** `docs/` 1,518 個檔裡 1,394 個是翻譯, 且覆蓋極度不均:
ja-JP 522, zh-CN 416, tr 142, es 142, ko-KR 64, zh-TW 58, pt-BR 47, vi-VN 1, ur 1, uk-UA 1, th 1.
翻譯與原文之間沒有同步檢查, 所以每一份都是一個獨立的過期面.

## 兩個分歧

分歧本身是發現, 記兩邊的立場與什麼能裁決, 不挑比較新的那個.

**主動派工 vs direct execution.** ECC: 「Use agents proactively without user prompt」,
「launch multiple agents simultaneously」, 且全 repo 沒有巢狀派工深度限制, 沒有 verifier 額度
(`grep -rni "nested subagent|depth limit|verifier quota"` 兩者皆空, 唯一命中是 `santa-method`
要求兩個 reviewer 都通過). 本專案: direct execution 為預設, 三項成本測試沒過就不派.
**裁決**: 本專案這一側有量測 —— replay 的 d3–d6 四對 cell 從 12 檔量到 96 檔, 派工成本是 inline
的 1.1–3.6 倍且交會點不存在 ([replay README Part 15](../../evals/replay/README.md)). ECC 這一側
沒有任何成本數字. 有量測的一側勝, 但這不是「ECC 錯」, 是**它的成本結構沒被量過**.
會推翻的觀察: 一個形狀讓 inline 成本超過派工 —— 至今四對 cell 沒出現.

**`--no-verify` 該不該擋.** ECC 擋 (`scripts/hooks/block-no-verify.js`, 14 KB, 連
`-c core.hooksPath=` 一起擋). 本專案**把它列為逃生口**: `docs/hook-system.md` 的 `githooks/pre-commit`
那列明寫逃生口是 `AGENT_SKIP_TEST_GATE=1` 或 `--no-verify`.
**裁決: 維持現狀, 因為前提不同.** ECC 的 pre-commit 是使用者專案的 hook, 助理繞過它等於繞過
使用者的規則; 本專案的 pre-commit 是本 repo 自己的測試閘, 而「刻意提交紅狀態」是本 repo 支援的
操作, 已有具名逃生口. 兩邊都認為「守衛不該被無聲繞過」, 差別只在誰擁有那個守衛.
而**兩邊都關不掉的那一段是同一段**: client 端的 git hook 本來就繞得過去, 真正關得起來的
那一層是 CI —— 所以這場分歧的賭注比它看起來小.
會推翻的觀察: 出現一次 `--no-verify` 被用來繞過**不屬於本 repo** 的 hook.

## 證據等級: 形狀可借, 數字一律不借

ECC 唯一帶效果數字的是 gateguard: skill description 寫「Measurably improves output quality by
+2.25 points vs ungated agents」. 讀 `skills/gateguard/SKILL.md:36-45` 的證據節:

- n = **2 個任務** (analytics module, webhook validator).
- 尺規是 1–10 主觀分, 沒有說誰評, 沒有 rubric, 沒有 run 數, 沒有變異.
- 兩題結果 +1.5 與 +3.0, 平均 +2.25 就是那兩題的平均.

**這個數字一個字都不能借**, 而且它出現的位置更值得記: 它寫在 skill 的 `description` 欄, 也就是
模型每次載入 skill 都會讀到的那一行. 一個未經校準的效果數字放在 prompt 表面上, 會讓模型把它
當事實引用. 本專案的對應規則是「上游的數字是它的契約在它的 client 上的觀察」—— 這是那條規則第一次
撞到「數字直接住在 prompt 裡」的情況, 值得在 `evidence-ladder` 記一句 (計畫 Q9b).

反過來, 它的**機轉描述**可以借, 因為那是可獨立驗證的因果主張, 不是量測結果:

> Instead of asking "are you sure?" (which LLMs always answer "yes"), this hook demands concrete
> facts: importers, public API, data schemas. The act of investigation creates awareness that
> self-evaluation never did.
> — `scripts/hooks/gateguard-fact-force.js:6-9`

## 沒有查的

- **286 個 skill 的內容**: 只讀了 `gateguard`, `continuous-learning-v2`, `santa-method`,
  `eval-harness` 四支的本體, 其餘只看目錄與 `origin:` 欄統計.
- **68 個 agent 與 94 個 command 的內容**: 只讀 `instinct-status`, `evolve`, `model-route` 三支,
  其餘只看 `AGENTS.md` 的清單.
- **277 支測試**: 只讀 `tests/ci/gateguard-env-documented.test.js` 一支.
- **`ecc2/` (Rust 重寫) 與 `research/ecc2-codebase-analysis.md`**: 未讀.
- **`docs/` 1,518 檔**: 只讀 `architecture/harness-adapter-compliance.md` 的產生器側; 翻譯全未讀.
- **`hooks.json` 41.7 KB 的內嵌 `node -e` 本體**: 只解析結構與 description, 逐支實作只讀了
  `scripts/hooks/` 下的 8 支.
- **上游的上游**: `zunoworks/gateguard` 本身沒有查, 所以 fact-forcing 的原始形狀與 ECC 改造了
  什麼, 本輪分不出來.
- **wording 對照**: 本輪只做覆蓋對照 (每條有沒有本地等價), 沒有做逐句用詞對照. 因為本輪沒有任何
  文字落進 `main/`, 授權面上還不需要; 計畫裡任何一項真的落地時, 那一輪要補做.

## 這一輪的機械追蹤缺口 (2026-09-08 已關)

**原本的缺口**: `scripts/upstream-pin-report.py` 只撿 research README 裡
**類別為「上游」**的列, 因為同業列的 SHA 可能是 path commit 而不是 repo head
(eli5 那列就是). ECC 是同業, 所以它不會被追蹤, 下次它動了沒有人會自動知道.

**解法比當時設想的小** (計畫 Q9): 不需要新欄位也不需要新標記. 兩種列本來就寫得不一樣 ——
ECC 寫 ``pin `<sha>``, eli5 寫 ``path 最後 commit 仍是 `<sha>`` —— 所以拿掉類別過濾之後,
既有的 `PIN_CELL` 自己就分得開. **判準因此從欄位換成句子**: ``pin `<sha>`` 是對整個 repo
的宣稱, ``path 最後 commit 仍是`` 是對一個目錄的宣稱, 只有前者比得起來. 而寫列的人可以
刻意滿足前者, `類別` 欄從來不行 —— 它說的是這個來源**對我方是什麼**, 不是它的 SHA 是什麼意思.

實跑 7 個 pin (原本 6), ECC 讀 `current`.

**仍然成立的那一半**: ECC 的更新頻率 (2026-09-07 一天 26 個 commit) 讓 pin 比對很快失去
意義 —— 被追蹤只回答「它動了沒」, 而對這種上游有價值的是**逐節重查**. pin-report 現在會
提醒, 但提醒的內容大概永遠是 `MOVED +N` 且 N 很大.

## 推翻條件

- **ECC 的資產計數在三份檔上被統一** → 三個反面觀察的第一條失去現況支撐, 但佐證仍成立 (它曾經發散).
- **`last_verified_at` 出現過期測試** → Q5 的設計要改成跟它同形而不是「它缺的那半」.
- **本機 `denials.jsonl` 的最長連擊在 Q2 落地前掉到 3 以下** → Q2 的三個量測數失效, 要重量再決定.
- **`zunoworks/gateguard` 查明 fact-forcing 是從別處來的** → 這條的血緣要再往上追一層, 計票不變
  (本輪就沒把它算成 ECC 的票).

## 升級計畫: 結案表與重開條件

2026-09-08 開的升級計畫已於 09-10 全部結案, 計畫頁 2026-09-15 退場 (全文由 Git 保存); 這一節接手它唯一還活著的內容 —— 重開條件與明確不做的清單. 十三項的處置與落地當天的數字在 [landing-log](landing-log.md#2026-09-08-ecc-計畫逐項結案-2026-09-10-自升級計畫搬入).

已落地: Q1 (hook 環境開關文件化, 雙向), Q2 (拒絕訊息衰減, 只做 `managed-target-guard`), Q5 (`deployment-verification.tsv` 旁側檔, 90 天到期), Q8b (逐閘宣告「什麼條件下等於沒有」), Q9 (`upstream-pin-report` 讀同業 pin), Q9b, Q10 (每支 skill 一份 `ATTRIBUTION.md`). 量過不做: Q3, Q3b, Q4, Q6, Q7, Q8.

### 重開條件

- **Q3 / Q3b / Q8**: 各自寫在 [mechanism-evidence-map](mechanism-evidence-map.md) 該節.
- **Q5**: 連續三個 90 天週期重新觀察都沒有任何一列的 client 停止讀取 → 到期改成 weekly-integrity 的 finding, 不再擋 commit.
- **Q6**: skill 失敗率量到超過 3%, 或出現一次「載入了但失敗」. 量法: transcript 的 `tool_use` 對 `tool_result` 配對掃描.
- **Q7**: 出現一次動了上限而 commit message 說不出理由.
- **Q9**: ECC 的更新頻率讓 pin 比對失去意義時, 改用查核日而不是 SHA.
- **Q10**: 任一支標「自有」的 skill 被查出一句蒸餾自他處 → 「自有」判準加一道對研究文的機械比對.

### 明確不做的 (依據在上面的逐條處置表)

- 四份常駐檔的拆法 (A1), prompt-defense baseline (A2), 80% 覆蓋率門檻 (A8): 加規則不加可失敗的檢查.
- instinct 信心分數與 `/evolve` 叢集 (C1, C5): 模型自評沒有校準來源; 本專案的 skill 是蒸餾產物不是生成物.
- `harness-audit` 式評分 rubric (D2): 分數上升會被讀成改善.
- 安裝 profile (F2), 多語系鏡像 (F3): 把「現在是什麼狀態」變成要對帳的東西.
- 擋 `--no-verify` (B7): 分歧, 見[兩個分歧](#兩個分歧).
- hook profile 分級 (B8), 治理事件另開一條 (E5), process group kill 與心跳 (E3): 沒有對應的執行面.
- MCP 斷路器 (B11), per-skill 健康度 (D1): 記為缺口不排, 沒有本機事故就不加閘.
