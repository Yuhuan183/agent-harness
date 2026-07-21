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

AA 的 GPT-5.6 發布分析另列：Sol／Terra／Luna max 的 Intelligence 為 59／55／51，
Cost per Intelligence Index Task 為 US$1.04／US$0.55／US$0.21；在 Codex harness 的 Coding
Agent Index 為 80／77／75。Sol max 的 coding task 成本約比 Claude Code 的 Fable 5 max
低 40%、比 Opus 4.8 max 低 10%。同一篇分析也指出，跨 effort 比較時 Sol 與 Luna 位於
Terra 前方的 Intelligence／Cost Pareto frontier。
<https://artificialanalysis.ai/articles/gpt-5-6-has-landed>

**不能從這些數字推出：**

- Fable 的 60 分是純 Fable 成績；該頁明示包含 Opus 4.8 fallback。
- max 的排序可直接證明本 repo 的 low/high 組合排序。
- 全套評測 API 成本除以任意題數就等於 Cost per Task；AA 會依各評測題數、重複次數、
  token 類型與 Index 權重計算。
- 基礎模型總分可取代 Coding Agent Index。後者測的是特定模型、agent harness 與設定。

方法與 coding-agent 頁：
<https://artificialanalysis.ai/methodology/intelligence-benchmarking>、
<https://artificialanalysis.ai/agents/coding-agents>。

## 成本模型

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
experience ledger 的同 role／provider 結果；樣本不足時才以 AA 的相近 task/harness 資料作先驗。
訂閱方案、基礎設施、人工監督及失敗損失不在 AA 的 pay-per-token Cost per Task 內，必須另算。

`experience-ledger` schema v2 會盡量自動取得 input、output、cache write/read token；品質檢查後
可補 review/rework 時間及 provider-reported API cost。舊紀錄或缺欄位時仍只能退回 `tokens_out`
與 subagent `secs`，不能換算或冒充完整美元成本。

## 對本專案的路由含意

- 模型選擇權仍屬使用者；repo 內 H/X、Sol/high、Opus 等名稱是可更新的操作參考，不是自動
  切換規則，也不是 AA 對該 exact effort 的證明。
- Repository 修改優先看 Coding Agent Index 與相近 component benchmark；研究、商業交付物、
  長 context、安全審查需改看對應能力與本機驗收，不用單一總榜包辦。
- 外部 benchmark 決定初始探索順序；`experience-ledger` 的 AR/CR/RB/FR、時間與 token 才負責
  更新本機 provider 偏好。模型或 harness 升級後，舊證據應衰減或重新抽樣。
- 高能力模型只有在提升可接受率、減少返工或降低失敗風險時才划算；機械任務不因總分高就
  自動升級，安全／金錢／破壞性資料也不因 token 價低就降級。

### 零樣本期的 CP 路由先驗

以下是本機 role/provider 樣本不足時的**探索起點**，不是已證明的固定路由。Artificial Analysis
顯示 GPT-5.6 Luna 與 Sol 橫跨 reasoning effort 位於 Intelligence／Cost Pareto frontier，而 Terra
被兩者支配；Coding Agent Index 的 max 設定為 Sol 80、Luna 75，但 Luna 每任務成本約低 80%。

| 工作 | 初始 CP 組合 | 升級條件 |
|---|---|---|
| 主 agent：一般 repository 工作 | GPT-5.6 Luna／medium | 架構分歧、高風險、跨系統整合 → Sol／high |
| 主 agent：重大 review、複雜除錯、安全／金錢邊界 | GPT-5.6 Sol／high | 一次性極高價值工作才另評估 max；本 harness 預設上限 high |
| `Explore` | GPT-5.6 Luna／low；Claude Haiku／low | 搜尋本身不做設計判斷，不因資料量升 effort |
| `mech-executor` | GPT-5.6 Luna／low；Claude Sonnet／low | pattern 出現例外就停止回主 agent，不自行升級 |
| `executor` | GPT-5.6 Luna／medium | 局部設計、高返工風險或重要整合 → Sol／high；Claude 明確選擇時 Opus／high |
| `plan-verifier`、`verifier` | GPT-5.6 Sol／high；Claude Opus／high | 保持與重大工作相稱的 challenge depth，不用廉價模型例行蓋章 |
| `security-reviewer`、`security-executor` | GPT-5.6 Sol／high | Claude Opus／high 僅作一次 fallback 或明確選擇 |

之所以不把 Terra 列為預設，是 AA 目前明示每個 Terra effort 都有 Luna 或 Sol 以不更高成本提供
更高能力，或以更低成本提供相近能力。Claude Fable 5 的絕對能力較高，但 max Index 全套評測
成本約為 Sol max 兩倍；沒有本機證據前，不把它當大量 leaf task 的 CP 預設。

## 仍待本機驗證

- 以 3–5 類真實任務分層抽樣：recon、mechanical implementation、judgment-heavy change、
  verification、security；每組記錄 exact model、effort、role、provider、outcome、wall-clock、
  token 與人工返工。
- 對相同 brief 做小規模交叉 provider 比較；避免用不同難度任務直接比較 AR 或成本。
- 使用 AA 快照時記錄日期、模型設定、harness、benchmark 版本與成本口徑；版本改變就重抓，
  不把排行榜數字寫成永久契約。
