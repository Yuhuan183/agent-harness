# Harness Engineering 研究摘要（2026-07）

現代 coding agent（Claude Code / Codex）是否仍需要 harness engineering、常駐指令檔該留
什麼，以及模型／provider 該如何用能力、時間與成本證據選擇的研究彙整。

## 結論與證據強度

仍需要 harness，但應把不同問題分層處理：

1. 常駐契約只保留每個 session 都需要、且模型推不出的規則。
2. 角色與工具流程用 skills 漸進揭露；可確定判斷交給 hooks/tests。
3. 外部 benchmark 只作先驗；實際路由以「同任務、同 harness、同 effort」的本機驗收率、
   wall-clock、token 與人工返工為主。
4. 最佳化目標不是每 token 最便宜，而是每個「可接受成果」的總成本最低。

本文標記三種證據：**已驗證**是可重查的一手來源或本 repo 測試；**推論**是從數據套用到
本專案；**啟發式**是待本機實驗驗證的維運門檻。

## 常駐指令與 context

**已驗證**

- Anthropic Claude Code Best Practices 建議以「刪掉會不會讓 Claude 犯錯」判斷內容去留，
  並警告肥大的 `CLAUDE.md` 會使重要指令被忽略。
  <https://code.claude.com/docs/en/best-practices>
- IFScale（arXiv 2507.11538）研究長指令集合下的遵循度衰退；可支持「規則會互相競爭
  注意力」，但不能單獨證明任何固定行數上限。<https://arxiv.org/abs/2507.11538>
- Chroma Context Rot 顯示模型可靠性可能隨 context 增長而非線性下降；長 context window
  不等於能無損利用全部內容。<https://research.trychroma.com/context-rot>
- Agent Skills 將按需內容與常駐 metadata 分離，適合承載不需每回合載入的流程。
  <https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills>

**推論**：本 repo 採短主契約、自足 leaf role、skills/docs 分流及 hooks/tests enforcement，
方向與上述證據一致。

**啟發式**：`CLAUDE.md`／`AGENTS.md` 目標 40–80 行、在 context 明顯膨脹時於收斂點壓縮。
這些是維運預算，不是已被證明的通用臨界值；應以真實任務回歸決定是否調整。

## Pilotfish v1.3.0 案例（2026-07-20）

**已驗證**：[`Nanako0129/pilotfish` v1.3.0](https://github.com/Nanako0129/pilotfish/releases/tag/v1.3.0)
對 v1.2.1 的核心政策增量很小，主要把兩場長時間實務 session 的失敗形狀轉成三條
backend-neutral guardrail；其餘大量變更是 policy tests、Baton compatibility Gate 與
[field report](https://github.com/Nanako0129/pilotfish/blob/v1.3.0/docs/field-report-tokscale-2026-07.zh-TW.md)。
tag commit 為 `bd6552f4bd4c3faa273cb4d15b31eace03c86ff4`，本次 checkout 的 19 項測試全數通過。

Field report 的精確計數顯示，一場 26 小時 session 有 1,267 次 main 直接編輯、12 次派工；
兩場合計 judgment tier 佔 92% output tokens，並使用 201 次 outcome verifier，其中約 42% 回覆
`REFUTED`，證明 fresh verification 有效，但平均每次不到六分鐘，粒度過細。`plan-verifier`
曾對 2 份 Plan 呼叫 24 次，`REVISE` 率 71%，顯示 readiness gate 也會產生 review churn。
外部 review 另曾在單一 PR 到第 6 輪，R2 後邊際收益已低。這些資料來自同一使用者、同一產品
家族、GPT-5.6 gateway 的兩場 session，不是 native Claude A/B，也不能推導通用派工次數、
review 輪數、成本或模型路由門檻。

v1.3.0 因此採用「可證明的工作形狀」而不是數字門檻：剩餘項目必須彼此獨立、同型，且一份
stable one-shot brief 能完整描述 goal、constraints、done criteria、ownership 與逐項 acceptance，
才可合批；已診斷且修法明確的 review finding 可視為 execution，但 main 仍保留例外、整合與驗收。
Outcome verifier 則移到能反駁完整主張的 smallest coherent integration boundary；security、FFI、
serialization／pre-aggregation、不可逆或會阻塞後續整合的邊界才提前驗。未實質變更的 Plan
不再重送，除非有 material revision 或新證據；分歧無法收斂時必須簡化、揭露 blocker 或延後 scope。

### 對本專案的取捨

| 類別 | 判斷 | 本地處理 |
|---|---|---|
| 值得借鑑 | recurrence 的 shape-based batching | 寫入 Claude Baton skill、brief reference 與 Codex resident contract，不設「做滿 N 次」門檻 |
| 值得借鑑 | coherent-boundary verification | focused checks 留作中間證據；fresh verifier 只在完整主張可反駁時啟動，特殊邊界提前驗 |
| 值得借鑑 | unchanged-Plan anti-churn | 重送必須有實質 revision 或新證據；未解分歧不得由 main 靜默推翻 |
| 已有等價 | direct-first、單一未知 bug reasoning chain、完成結果直接收回、scope／ownership／stop boundary | 保留現行契約，不複製 Pilotfish 文字與 phase ceremony |
| 已有等價 | 可重現部署證據 | 本專案用 manifest、transactional sync、parity 與 contract tests；不另引入 marker-block installer |
| 不採用 | 固定 `best`／fallbackModel、固定八角色與模型 aliases | 主模型仍由使用者掌控；沿用本地七角色、quality floor 與 experience-ledger |
| 不採用 | 用單次 client cost 或 field 次數直接改 routing | client cost 只算觀察值；route 仍需同 cohort、同 harness、可接受成果與 revision policy 證據 |

Pilotfish 的 Baton release Gate 另證明政策 bytes 與執行證據可以一起封存：成功 candidate 記錄
policy／prompt SHA-256、invocation、唯一寫入、測試與 verifier verdict；中斷與 superseded candidate
仍保留但不冒充 final evidence。其成功 Gate 的 client 欄位為 US$3.5088455、wall time 323.978 秒，
只證明 compatibility／provenance，不證明 native-Claude 成本或效率。本專案借用的是「證據分級與
失敗紀錄不漂白」的精神，實作上沿用既有 deployment manifest、ledger eligibility 與 parity checks。

## Artificial Analysis 快照（2026-07-21）

Artificial Analysis Intelligence Index v4.1 是英文、純文字的綜合評測，共 9 項：Agents 34%、
Coding 24%、Scientific Reasoning 24%、General 18%。GDPval-AA v2 與 tau3-Banking 佔 34%，
因此總分不是 coding agent 成功率，也不是「正確率百分比」。方法頁估計 Index 的 95% 信賴
區間小於正負 1%，但個別評測可能更寬。

| 模型／設定 | Index | 速度 tok/s | API input/output（每 1M） | Index 輸出量 | 全套評測 API 成本 |
|---|---:|---:|---:|---:|---:|
| Claude Fable 5 max，含 Opus 4.8 fallback | 60 | 68.3 | US$10 / US$50 | 87M | US$5,630.52 |
| GPT-5.6 Sol max | 59 | 63.4 | US$5 / US$30 | 70M | US$2,824.18 |
| GPT-5.6 Sol high | 56 | 58.7 | US$5 / US$30 | 21M | US$955.55 |
| Claude Opus 4.8 max | 56 | 59.9 | US$5 / US$25 | 120M | US$3,752.55 |
| Claude Sonnet 5 max | 53 | 83.9 | US$2 / US$10 | 300M | US$4,010.12 |
| Claude 4.5 Haiku reasoning | 30 | 104.8 | US$1 / US$5 | 88M | US$538.77 |

資料頁：
[Fable 5](https://artificialanalysis.ai/models/claude-fable-5)、
[Sol max](https://artificialanalysis.ai/models/gpt-5-6-sol)、
[Sol high](https://artificialanalysis.ai/models/gpt-5-6-sol-high)、
[Opus 4.8](https://artificialanalysis.ai/models/claude-opus-4-8)、
[Sonnet 5](https://artificialanalysis.ai/models/claude-sonnet-5)、
[Haiku 4.5](https://artificialanalysis.ai/models/claude-4-5-haiku-reasoning)。

AA 的 GPT-5.6 發布文章曾列 Sol／Terra／Luna max 的 Cost per Intelligence Index Task 為
US$1.04／US$0.55／US$0.21；目前 v4.1 模型頁重算後是 US$1.04／US$0.82／US$0.21，故 Terra
的 US$0.55 已過時。發布文章中的 Codex Coding Agent Index 80／77／75 仍是另一個 harness
評測，不能與下表的基礎模型 Index 混用。

目前模型頁的完整 effort 快照如下。每格依序是 `Index／美元每 Index task／加權 decode 分鐘／
output token 每 Index task`；decode 時間排除 TTFT、工具與其他平台 overhead，不是端到端時間。

| Effort | Sol | Terra | Luna |
|---|---:|---:|---:|
| low | 49.44／$0.197／0.773／2,508 | 40.47／$0.154／0.267／2,258 | 33.26／$0.040／0.194／2,298 |
| medium | 53.59／$0.314／1.234／4,203 | 45.57／$0.175／0.458／3,769 | 38.05／$0.050／0.315／3,663 |
| high | 55.87／$0.453／1.833／6,690 | 48.95／$0.336／0.940／7,738 | 46.06／$0.095／0.699／8,118 |
| xhigh | 57.65／$0.682／2.710／9,941 | 51.60／$0.477／1.350／11,036 | 49.07／$0.139／1.049／12,492 |
| max | 58.89／$1.037／4.152／15,346 | 54.95／$0.825／2.056／19,370 | 51.24／$0.209／1.571／18,912 |

資料頁：
[Sol](https://artificialanalysis.ai/models/gpt-5-6-sol)、
[Terra](https://artificialanalysis.ai/models/gpt-5-6-terra)、
[Luna](https://artificialanalysis.ai/models/gpt-5-6-luna)、
[發布文章](https://artificialanalysis.ai/articles/gpt-5-6-has-landed)。

**不能從這些數字推出：**

- Fable 的 60 分是純 Fable 成績；該頁明示包含 Opus 4.8 fallback。
- max 的排序可直接證明本 repo 的 low/high 組合排序。
- 全套評測 API 成本除以任意題數就等於 Cost per Task；AA 會依各評測題數、重複次數、
  token 類型與 Index 權重計算。
- 基礎模型總分可取代 Coding Agent Index。後者測的是特定模型、agent harness 與設定。

方法與 coding-agent 頁：
<https://artificialanalysis.ai/methodology/intelligence-benchmarking>、
<https://artificialanalysis.ai/agents/coding-agents>。

## 從 benchmark 到 routing 的決策框架

### 成本口徑

單次 API 成本：

```text
C_api = (Tin*Pin + Tcache_write*Pwrite + Tcache_read*Pread + Tout*Pout) / 1,000,000
```

實務路由應比較：

```text
expected_total_cost
  = run_cost / P(acceptable outcome)
  + human_review_and_rework
  + latency_value
  + residual_failure_risk
```

這不是精確會計公式，而是避免只看單價的決策框架。`P(acceptable outcome)` 優先取本機
experience ledger 中同 role／task class／目前 route cell 的結果；樣本不足時才以 AA 的相近
task／harness 資料作先驗。
訂閱方案、基礎設施、人工監督及失敗損失不在 AA 的 pay-per-token Cost per Task 內，必須另算。

`experience-ledger` schema v3 會記錄請求來源（Claude Code、native Codex、Claude Code 的 Codex
plugin）、dispatch／rollout 識別碼，並盡量自動取得 input、output、cache write/read token；品質
檢查後可補 review/rework 時間及 provider-reported API cost。舊紀錄或缺欄位時仍只能顯示較窄
的代理值，不能拿 total token 與 output-only token 互比，也不能冒充完整美元成本。

### 本專案如何使用這些證據

- 模型選擇權仍屬使用者；repo 內的模型與 effort 是有日期的操作先驗，不是執行中自動切換規則，
  也不是 AA 對 Claude exact effort 的證明。
- Repository 修改優先看 Coding Agent Index 與相近 component benchmark；研究、商業交付物、
  長 context、安全審查需改看對應能力與本機驗收，不用單一總榜包辦。
- 外部 benchmark 決定初始探索順序；`experience-ledger` 的 AR/CR/RB/FR、時間與 token 才負責
  更新本機 provider 偏好。模型或 harness 升級後，舊證據應衰減或重新抽樣。
- 高能力模型只有在提升可接受率、減少返工或降低失敗風險時才划算；機械任務不因總分高就
  自動升級，安全／金錢／破壞性資料也不因 token 價低就降級。

Main 與七個 leaf roles 的責任、三種 profile 語意及各 surface 套用方式已由
[根 README](../README.md#執行模型) 統一說明；現行 pins、品質門檻與 availability 的唯一真相源是
[Claude routing](../.claude/model-routing.toml) 與 [Codex routing](../.codex/model-routing.toml)，
研究摘要不再複製容易過期的 route 表格與操作命令。

2026-07-22 快照下的決策理由：

- 快速表示「通過品質門檻後最快」，不是所有候選中絕對最快。
- 沒有獨立 `economy` profile。「較省」由 provider 選擇、訂閱額度與每個可接受成果的本機成本
  決定，不能靠降低品質門檻達成。Luna／high 的 AA API 成本代理雖比 Terra／low 低約 39%，但
  decode 約慢 2.6 倍、benchmark output token 約為 3.6 倍；而訂閱額度沒有公開美元換算公式。
- Codex `balanced` 的 support roles 使用 Sol／low，付出一些時間與成本換額外能力餘裕；judgment
  與 critical roles 已位於品質門檻，不任意降級。
- 在 GPT 候選中，`Sol/high` 的 high 設定分數最高且 output token 最少，因此 Codex critical roles
  使用它；Claude critical roles 另由 Claude routing 的 Opus 品質門檻決定。
- Luna native leaf 與 Claude bridge 路徑雖已驗證，但現行 profile 不選 Luna；availability 不等於
  routing recommendation。若日後啟用 native Luna，仍需 routing 檔標示的 `agent_config` delivery，
  不能假設 `spawn_agent.model` 原生接受。

Claude 與 Codex 使用相同的三種策略語意，但各有自己的 routing 檔。Claude 原生 leaf 的 profile
是 deployment preset：先在 source checkout 用 `activate-profile` 一次更新所有 frontmatter pins，
再 sync、開新 session；不是每次派工切換。native Codex 與透過 `codex:codex-rescue` 呼叫的 Codex
twin 則是 per-dispatch route，後者以 `resolve --surface claude-bridge` 取得 model／effort。兩者都
不會改變 main 模型；resolver 缺失、設定無效或回傳不可派模型時停止該次 Codex leaf。

Codex 官方手冊也建議一般 demanding agent 從 GPT-5.6 開始，而 read-heavy scan／supporting
documents 可用 Terra；custom agent 可省略 model／effort 繼承，或在派工時明確指定。這支持
profile 在 main task 解析、leaf role 檔不硬編 model／effort 的做法。
<https://learn.chatgpt.com/docs/agent-configuration/subagents>

Claude Fable 5 的絕對能力較高，但 max Index 全套評測成本約為 Sol max 兩倍；沒有本機證據前，
不把它當大量 leaf task 的 CP 預設。

## 本機案例：review 深度的檔位實驗（2026-07-22，pixi-game-framework）

**已驗證**（一手資料：同一 repo、同一天、三輪 review，全部發現經 main session 對照原始碼
逐條覆核；帳本有對應 17 筆 `Explore × claude` 記錄）。

外部先驗只能提供方向：AA v4.1 的 max 設定為 Fable 60、Sonnet 53，相差 7 個 Index points；
但 Fable 成績含 Opus 4.8 fallback，Index 也不是 repository-review benchmark，且沒有本案例
`medium` effort 的同口徑公開矩陣。因此下列本機結果不能拿 AA 分差校正，也不能把兩者合併成
一個「review 品質分數」。

| 輪次 | Route | 切分方式 | 產出 |
|---|---|---|---|
| R1 | Sonnet／low ×6 | 審查維度（架構/契約/代碼/測試/文檔/現代化） | 1 Major（usePressable 多指）；2 個 agent 交出錯誤候選被 main 駁回 |
| R2 | Sonnet／medium ×5 | R1 申報的覆蓋缺口 | 0 缺陷；誠實申報殘餘未驗面 |
| R3 | Fable／medium ×6 | 全新視角：對抗 interleaving、數學重推導、對照安裝版引擎原始碼、全測試逐 assertion | 1 HIGH（refcount 永久洩漏）+ 3 Major（渲染鏡射/平鋪/遮罩）+ 2 個 stage 重入洞 + 約 20 項次要，全部屬實 |

R3 翻出的重大缺陷集中在**跨系統語意接縫**：test mock vs 真實引擎 setter 語意、
`act()` vs 真實 Scheduler 的 cleanup 順序、同步 emit 窗口的世代交接。R1/R2 驗的是「程式碼
自身的一致性」（這部分它們做對了——R3 的對抗劇本絕大多數也被既有防護擋下）；R3 額外做到的
是把接縫兩側的語意同時載入並從頭重推。本次 Sonnet 輪次的實際缺口不是「掃得不夠多」，而是
**沒有主動質疑另一側系統的語意**；這是本案例觀察，不是 Sonnet 的通用能力上限。

**混淆因子（誠實標註）**：R3 同時換了模型與 brief 設計——brief 明示「不要信任前輪結論、
重新推導、mock 可能說謊、構造具體 interleaving」。無法把差距全歸因於模型檔位；且 R3 的
brief 正是靠 R1/R2 的覆蓋申報累積出來的，三輪是遞進而非平行對照。

帳本原始遙測也顯示，Fable 的深度不是免費取得。下表是 child duration 與 token 欄位的描述統計；
agent 有平行執行，所以 `secs` 加總不是主 session 的端到端時間。`total tokens` 包含 input、output、
cache write/read，適合描述本輪資源量級，不等於訂閱額度或可驗證美元成本。

| Route | outcome | 平均 child duration | 平均 output tokens | 平均 total tokens |
|---|---:|---:|---:|---:|
| Sonnet／low | 4 accepted／2 corrected | 52 秒 | 1,588 | 210,651 |
| Sonnet／medium | 5 accepted／0 corrected | 76 秒 | 2,564 | 505,499 |
| Fable／medium | 6 accepted／0 corrected | 569 秒 | 21,385 | 4,585,037 |

相較 Sonnet／medium，Fable／medium 在本輪平均約使用 7.5 倍 child duration、8.3 倍 output token、
9.1 倍 total token。它同時找出較多新的重大缺陷，但不能由此計算兩模型的 recall 或每個成功成果
成本：三輪沒有使用相同 brief、相同待找缺陷集合，也沒有 provider-reported API cost。這 17 筆
仍是 schema v2 legacy 紀錄，會留在 observed 統計，但依現行 revision policy 全數不得用來自動
改寫 route。

### 已吸收的做法與尚不能下的結論

- 已落地：專案審查使用 `task_class: review`，定位／盤點維持 `recon`；brief 用 scenario／lens
  指定 semantic seam、真實 runtime、排程與測試有效性，不再為題材新增 role。
- 已落地：schema v2 的 17 筆紀錄只留在 observed 統計，不回填、不遷移，也不參與 route revision。
- 尚不能下結論：R3 同時換模型與 brief，不能證明 Fable 的通用 recall，也不能據此建立
  `deep-review` role／profile 或改動日常 route。
- 下一個可判決實驗：對同一批已知或種入缺陷使用同一 brief、工具權限與停止條件，隨機分派兩條
  route；每個 route cell 至少 10 筆後，再比較重大缺陷 recall、誤報率、review／rework 時間與 token。

## 仍待本機驗證

- 以 3–5 類真實任務分層抽樣：recon、mechanical implementation、judgment-heavy change、
  verification、security；每組記錄 exact model、effort、role、provider、request source、outcome、
  wall-clock、token 與人工返工。`revision_policy` 目前設定為 90 天視窗、45 天半衰期、每個
  role × task class × route cell 至少 10 筆、P(win)≥0.90；兩側設定不同時工具停止。
- 對相同 brief 做小規模交叉 provider 比較；避免用不同難度任務直接比較 AR 或成本。
- 使用 AA 快照時記錄日期、模型設定、harness、benchmark 版本與成本口徑；版本改變就重抓，
  不把排行榜數字寫成永久契約。
