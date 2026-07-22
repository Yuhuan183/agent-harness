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
experience ledger 中同 role／task class／目前 route cell 的結果；樣本不足時才以 AA 的相近
task／harness 資料作先驗。
訂閱方案、基礎設施、人工監督及失敗損失不在 AA 的 pay-per-token Cost per Task 內，必須另算。

`experience-ledger` schema v3 會記錄請求來源（Claude Code、native Codex、Claude Code 的 Codex
plugin）、dispatch／rollout 識別碼，並盡量自動取得 input、output、cache write/read token；品質
檢查後可補 review/rework 時間及 provider-reported API cost。舊紀錄或缺欄位時仍只能顯示較窄
的代理值，不能拿 total token 與 output-only token 互比，也不能冒充完整美元成本。

## 對本專案的路由含意

- 模型選擇權仍屬使用者；repo 內 H/X、Sol/high、Opus 等名稱是可更新的操作參考，不是自動
  切換規則，也不是 AA 對該 exact effort 的證明。
- Repository 修改優先看 Coding Agent Index 與相近 component benchmark；研究、商業交付物、
  長 context、安全審查需改看對應能力與本機驗收，不用單一總榜包辦。
- 外部 benchmark 決定初始探索順序；`experience-ledger` 的 AR/CR/RB/FR、時間與 token 才負責
  更新本機 provider 偏好。模型或 harness 升級後，舊證據應衰減或重新抽樣。
- 高能力模型只有在提升可接受率、減少返工或降低失敗風險時才划算；機械任務不因總分高就
  自動升級，安全／金錢／破壞性資料也不因 token 價低就降級。

### Main 與 leaf role 的責任差異

Main 不是單純派工器。它持有完整使用者意圖與專案脈絡，負責問題定義、消除歧義、風險分類、
架構與取捨、是否派工、工作切界、整合所有結果、最終驗證及對使用者負責。直接執行仍是預設；
只有平行性、context 隔離或 fresh-context 獨立性明顯值得成本時才派 leaf。

| 角色 | 接收什麼 | 擁有的判斷 | 明確不負責 |
|---|---|---|---|
| main | 完整需求、repo 狀態、所有結果 | 架構、優先序、風險、整合、最終判決 | 不把最終責任下放 |
| `explore` | 一個明確的查找問題 | 搜尋路徑與證據整理 | 不設計、不修改、不決策 |
| `mech-executor` | 完整 pattern、範圍、完成條件 | pattern 內的機械套用 | 遇例外即停，不重新設計 |
| `executor` | 已封閉的目標、限制、scope | scope 內的局部設計與實作 | 不擴 scope、不改架構方向 |
| `plan-verifier` | 一份 material Plan | 對抗檢查假設、順序、ownership、驗收 | 不代寫 Plan、不實作 |
| `verifier` | 已完成的成果與聲稱 | fresh-context 反證與最終 gate 證據 | 不修復發現的問題 |
| security roles | trust boundary、abuse case、核准範圍 | 安全分析或核准後實作 | reviewer 不實作；executor 不重開分析 |

因此 main 與 executor 都可能用 Sol／medium 或 Sol／high，但原因不同：main 的強度由整體歧義、
整合與失敗影響決定；executor 的強度由已封閉子問題內仍需多少局部判斷決定。相同 model／effort
不代表責任相同，也不表示 executor 能取代 main。

Main route 是開啟 task 前的建議，因為執行中的 main 不能靠此設定自動換模型；leaf route 依
resolver 的 `invocation` 決定使用 spawn argument 或 custom agent config。部署後用
`${CODEX_HOME:-$HOME/.codex}/scripts/model-routing`，source checkout 內才使用
`.codex/scripts/model-routing`。

### 結構化 CP 路由先驗

`.codex/model-routing.toml` 保存 AA 數據、角色品質門檻與三組 profile，
`.codex/scripts/model-routing` 負責驗證與 per-dispatch 解析。選擇分兩階段：先通過角色品質門檻，
再在合格組合中最佳化速度、風險防護或均衡；不允許用次要目標交換門檻以下的品質。

| 品質層級 | 角色 | 目前允許的最低 route |
|---|---|---|
| `support` | `explore`、`mech-executor` | Terra／low |
| `judgment` | main、`executor`、`plan-verifier` | Sol／medium |
| `critical` | `verifier`、security roles | Sol／high |

| Profile／優先策略 | main | native `explore`／mechanical | Claude bridge support | `executor`／plan | critical |
|---|---|---|---|---|---|
| `balanced`（均衡） | Sol／medium | Sol／low | Sol／low | Sol／medium | Sol／high |
| `fast`（快速） | Sol／medium | Terra／low | Terra／low | Sol／medium | Sol／high |
| `quality_guarded`（高風險防護） | Sol／high | Sol／low | Sol／low | Sol／high | Sol／high |

目前三個 profile 都不選 Luna；support routes 使用 Terra／low 或 Sol／low。Luna native leaf 已在
Codex CLI 0.144.6 透過臨時 custom agent type 實測，Claude bridge 的 Luna／low 也已經 rollout
驗證，但現行 profile 不採用，故不保留未使用的 Luna 專用 role。這是路由決策，不代表
`spawn_agent.model` 已原生接受 Luna；若未來重新啟用 native Luna，仍需 `agent_config` delivery。

關鍵取捨：

- 快速表示「通過品質門檻後最快」，不是所有候選中絕對最快。
- 沒有獨立 `economy` profile。「較省」由 provider 選擇、訂閱額度與每個可接受成果的本機成本
  決定，不能靠降低品質門檻達成。Luna／high 的 AA API 成本代理雖比 Terra／low 低約 39%，但
  decode 約慢 2.6 倍、benchmark output token 約為 3.6 倍；而訂閱額度沒有公開美元換算公式。
- 均衡在 support roles 使用 Sol／low，付出一些時間與成本換額外能力餘裕；judgment 與
  critical roles 則已位於品質門檻上，不任意降級。
- `Sol/high` 在三個 high 版本中分數最高且 output token 最少，所以 critical roles 固定使用它。
- 官方定價頁列出 Plus 可使用 Sol／Terra／Luna，但訂閱／main selector 與 leaf override 是
  不同介面。設定分別記錄 `subscription`、`main_selector`、`native_leaf_override`、
  `claude_bridge_override`。Luna 前兩者為 `documented`，native leaf 經實測標為 `agent_config`；
  bridge 經 rollout 驗證為 `configured`。Sol／Terra 原生 leaf 則可用 `spawn_argument`。

Claude 與 Codex 使用相同的三種策略語意，但各有自己的 routing 檔。Claude 原生 leaf 的 profile
是 deployment preset：先在 source checkout 用 `activate-profile` 一次更新所有 frontmatter pins，
再 sync、開新 session；不是每次派工切換。native Codex 與透過 `codex:codex-rescue` 呼叫的 Codex
twin 則是 per-dispatch route，後者以 `resolve --surface claude-bridge` 取得 model／effort。兩者都
不會改變 main 模型；resolver 缺失、設定無效或回傳不可派模型時停止該次 Codex leaf。

Codex 官方手冊也建議一般 demanding agent 從 GPT-5.6 開始，而 read-heavy scan／supporting
documents 可用 Terra；custom agent 可省略 model／effort 繼承，或在派工時明確指定。這支持
profile 在 main task 解析、leaf role 檔不硬編 model／effort 的做法。
<https://learn.chatgpt.com/docs/agent-configuration/subagents>

```bash
.codex/scripts/model-routing list
.codex/scripts/model-routing resolve --profile balanced --role executor
.codex/scripts/model-routing resolve --priority fast --role executor
.codex/scripts/model-routing resolve --surface claude-bridge --priority fast --role explore
.codex/scripts/model-routing resolve --priority quality-guarded --role executor
.codex/scripts/model-routing validate
.claude/scripts/model-routing activate-profile --profile fast --dry-run
.claude/scripts/model-routing check-pins
```

Claude Fable 5 的絕對能力較高，但 max Index 全套評測成本約為 Sol max 兩倍；沒有本機證據前，
不把它當大量 leaf task 的 CP 預設。

## 仍待本機驗證

- 以 3–5 類真實任務分層抽樣：recon、mechanical implementation、judgment-heavy change、
  verification、security；每組記錄 exact model、effort、role、provider、request source、outcome、
  wall-clock、token 與人工返工。`revision_policy` 目前設定為 90 天視窗、45 天半衰期、每個
  role × task class × route cell 至少 10 筆、P(win)≥0.90；兩側設定不同時工具停止。
- 對相同 brief 做小規模交叉 provider 比較；避免用不同難度任務直接比較 AR 或成本。
- 使用 AA 快照時記錄日期、模型設定、harness、benchmark 版本與成本口徑；版本改變就重抓，
  不把排行榜數字寫成永久契約。
