# 常駐指令與供應商指引

[← 回研究摘要入口](README.md)

## 常駐指令與 context

**已驗證**

- Anthropic Claude Code Best Practices 建議用一個問題判斷內容去留:「刪掉它會不會讓 Claude
  犯錯」;並警告肥大的 `CLAUDE.md` 會讓重要指令被淹沒。
  <https://code.claude.com/docs/en/best-practices>
- IFScale(arXiv 2507.11538)研究長指令集合下遵循度怎麼衰退;它能佐證「規則會互相搶注意力」,
  但單靠它證不出任何固定的行數上限。<https://arxiv.org/abs/2507.11538>
- Chroma Context Rot 顯示模型的可靠性可能隨 context 變長而非線性下滑;context window 大,
  不代表能無損用完裡面的每一段。<https://research.trychroma.com/context-rot>
- Agent Skills 把「按需載入的內容」和「常駐的 metadata」分開,適合承載那些不必每回合都載入的
  流程。<https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills>

**推論**:本 repo 用短主契約、自足的 leaf role、skills/docs 分流、以及 hooks/tests 強制,
方向和上面這些證據一致。

**啟發式**:`CLAUDE.md`／`AGENTS.md` 目標抓 40–80 行,context 明顯膨脹時就在收斂點壓縮。
這是維運預算,不是已被證明的通用臨界值;要不要調,看真實任務回歸的結果。

## 實際量測與操作分級（2026-07-28）

**已驗證的容量**:目前
[Claude Fable 5、Opus 5、Sonnet 5 與 Opus 4.8](https://platform.claude.com/docs/en/about-claude/models/overview)
官方 context window 都是 1M tokens；Codex 使用的
[GPT-5.6 Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol)官方 context window 是 1,050,000 tokens
（最大 input 922,000、最大 output 128,000）。容量只是硬上限，不代表接近上限時仍能無損
保留每條規則的注意力。

本 repo 現在提供兩種不同但同口徑的診斷：

```bash
# Claude：最近 7 天每回合 prompt-context P50/P95，並列出壓力最高的 sessions
~/.claude/scripts/usage-report --days 7 --by-session --top 20

# Codex：最近一回合實際占用、剩餘 context，以及帳號 quota
~/.codex/skills/experience-ledger/scripts/codex-usage
```

| 占用 | 分級 | 操作 |
|---:|---|---|
| `<30%` | low | 不需額外動作 |
| `30–<50%` | watch | 保持單一主題，階段邊界留下 checkpoint |
| `50–<65%` | checkpoint | 換階段前先收斂，避免再灌入無關大型輸出 |
| `>=65%` | compact | 關鍵判斷前 compact，或從 checkpoint 開新 session |

這組數字是**專案操作啟發式**，不是供應商公布的故障線。它刻意在硬上限前預警，理由是上面的
context-rot 證據與本專案的多層契約形狀；後續應拿 P95 與返工／漏規則案例一起校準。

**口徑邊界**：

- Claude transcript 沒有直接寫「本回合已占 window 幾成」；報表以該 assistant turn 的
  `input_tokens + cache_creation_input_tokens + cache_read_input_tokens` 當 prompt-context
  代理值，輸出 P50/P95。未知舊模型先用保守的 200k；已知實際容量時用
  `--context-window` 覆寫。
- Codex rollout 已提供 `last_token_usage.total_tokens` 與 `model_context_window`，所以用兩者
  算最近一回合占用。`total_token_usage` 是整個 session 累計消耗，只能看成本，不能拿來當
  當前 context occupancy。
- account quota（例如 5h／weekly window）是能不能繼續呼叫的限制；attention pressure 是
  單次判斷是否可能被長 context 稀釋。兩者都要看，但不能互相替代。

**本機基準快照（2026-07-28，最近 7 天）**：

| 路徑 | P50 | P95 | 判讀 |
|---|---:|---:|---|
| Claude main／Fable 5 | 22.8% | 51.9% | 一般回合不高，但長 session 已進 checkpoint 區 |
| Claude main／Opus 5 | 28.9% | 86.0% | 尾端明顯過長，關鍵判斷前應 compact／換 session |
| Claude subagent／Opus 5 | 12.8% | 19.8% | leaf context 保持在低區，context protection 有實際差異 |
| Claude subagent／Sonnet 5 | 4.8% | 11.6% | leaf context 低 |

同一時間的 Codex rollout 回報有效 `model_context_window=258,400`，最近一回合約
59.2k／22.9%，屬 low；整個 session 累計約 56.0M tokens，證明累計量若誤當占用會得出完全
錯誤的警報。這個 258,400 是**當下 Codex runtime 的實際限制**，操作判斷優先於上面
GPT-5.6 Sol API 頁面的產品容量；snapshot 會隨 runtime、模型與 session 更新，應以指令重查。

## 供應商官方指引（2026-07）

同一週裡,兩家把「常駐指令要瘦」從社群經驗法則升級成帶數字的官方立場。兩份都是**一手來源**,
但數字都是**供應商自評**:沒有公開 harness、題目和計分細節,所以等級是「已驗證的官方主張」,
不是能獨立重跑的實驗。

### Anthropic：Claude 5 世代的 context engineering（2026-07-24）

<https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models>

**官方數字**:為 Opus 5／Fable 5 等 Claude 5 世代模型,把 Claude Code system prompt 刪掉
**80% 以上**,coding evaluations **量不到損失**。

文章列出的「昔非今是」對照本 repo:

| 舊做法 → 新做法 | 本 repo 現況 |
|---|---|
| 給規則 → 讓模型用判斷 | 已對齊(短契約、判準「刪掉會不會犯錯」);本次補上**矛盾**這個獨立的失敗形態 |
| 給範例 → 設計介面(漸進揭露、工具 deferred loading／`ToolSearch`) | 已對齊(skills＋`references/`;本 session 就是用 ToolSearch 載入工具) |
| 到處重複 → 工具用法寫進工具描述 | **部分做不到**:本 repo 只 deploy 全域契約,改不了供應商的工具描述;RTK／Headroom 因此各留一行觸發句 |
| CLAUDE.md 當記憶 → CLI 自動記憶 | **新增分工**:記憶層寫進 playbook 的分工表,常駐契約不再扛「怕忘記」 |
| 簡單 spec → 豐富參照(code、測試套件當 spec、rubric＋dynamic workflow) | 已有等價實作:trap fixture＋機械 grader 就是「測試當 spec」與 rubric;本次把「brief 指向 grader 勝過複述判準」寫成規則 |

文章對 CLAUDE.md 的具體建議:保持輕量、把 token 花在**程式庫的陷阱**上、**不要寫模型翻一下
repo 就知道的事**、多用漸進揭露。對 skills 的建議:當它是輕量指南,不是緊箍咒,除非那個領域
確實高風險。另外提供 `claude doctor`／`/doctor` 自動評估 skills 和 CLAUDE.md 的肥瘦。

其中「不要寫可推斷的事」和「skill 不要過度約束」本 repo 早就成文;真正**新增**的是矛盾成本
(見下)和記憶層的分工。文章舉的失敗例子,正是本 repo 的風險形狀:同一次請求裡,一邊寫
「文件留得合宜」、另一邊寫「不要加註解」。

**2026-07-26 稽核結果(已驗證)**:拿當期 Claude Code system prompt 逐條比對
`CLAUDE.contract.md` 的五條 working agreement 和三條 main-only 條款,**沒牴觸、沒重述**——
重述早在 52b434b 就清掉了,剩下的每一條(繁中回覆、`DECISION:` 標記、最窄驗證、保留 dirty
worktree、派工剎車)system prompt 都沒有涵蓋。所以這次整合**不動常駐契約**,落點是
[契約瘦身規範](../contract-slimming.md)的原則 2b 和內容判定表:管的是**下一次**改契約時的
判準,不是現在多加幾句。這本身就是文章的建議:先找矛盾,找不到就別動。

### OpenAI：GPT-5.6 model guidance（讀取 2026-07-26）

<https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.6#prompting-best-practices>

**官方數字**:在內部 coding-agent eval 上,精簡 system prompt 讓評分升約 **10–15%**、
總 token 降 **41–66%**、成本降 **33–67%**(官方註明是方向性區間,要自己驗)。

對本 repo 直接有後果的四條:

1. **矛盾比缺漏貴。** GPT-5.6 嚴格遵守 prompt contract,碰到互相衝突的規則會花 reasoning
   token 去調和,而不是擇一,結果更慢、更貴、更常錯。這和 Anthropic 那篇的實例互相佐證,
   已寫進 playbook §1 和契約瘦身規範。
2. **不要重複「先問過再動」。** 官方點名:重複這類話會對安全、預期內的動作觸發多餘的
   確認請求;正解是明確列出安全的本地動作、政策只放一處、每條只講一次。
   `AGENTS.contract.md` 第 8–9 行已經是這個形狀(先列出免授權的安全動作,再把授權邊界
   `stated once here`)。**2026-07-26 逐檔稽核結論:無違反。** 唯一看起來像重複的,是 AUTH
   條款在 `executor`／`mech-executor`／`security-executor` 三個 role TOML 各出現一次——
   但那是三份**自足、互斥載入**的角色契約,一個 leaf 永遠只看到其中一份,不算官方所指的
   「同一個 prompt 內重複」。記在這裡,免得日後有人當它冗餘刪掉,拆掉自足性。
3. **`text.verbosity` 與「盡量簡短」。** GPT-5.6 預設就比 5.5 精簡,籠統的簡短指令可能多餘,
   甚至讓回覆過短;要留就得指名保留什麼、捨棄什麼。兩份契約現行的
   「Lead with the outcome. Keep conversation proportional and requested artifacts complete.」
   已經是這個形狀(同時指名保留什麼、可壓縮什麼),不必改寫;規則本身已反映到 playbook §4。
4. **effort 階梯的官方定位**:`medium` 是平衡起點、`low` 給延遲敏感、`high`／`xhigh` 只在
   量得到品質增益時用、`max` 留給最難的品質優先工作,而且該跟 `xhigh` 對比,別預設它更好。
   本 repo 的三個 profile 本來就沒有任何角色釘到 `high` 以上,方向一致;已記入
   `main/codex/model-routing.toml` 的 `model_guidance_source`。

**刻意沒做的事**:Programmatic Tool Calling、multi-agent [beta]、`reasoning.mode: "pro"`、
explicit prompt caching 和 `reasoning.context` 都是 Responses API 的能力。本 bundle 透過
Codex CLI 派工,這些參數不在可控面上,所以只記錄、不接線;`none` effort 同理(見
[2026-07-26 AA 節](model-evidence.md#artificial-analysis-重新取數完整-effort-階梯2026-07-26)
結論 4)。

**共同結論(推論)**:兩家的建議在本 repo 收斂成同一條維運規則——**加規則前先找矛盾**。
本 repo 現有的預算機制(`word_count` 上限)只擋得住肥大,擋不住矛盾;矛盾要靠
「同一政策只有一個真相源」＋twin-parity 測試＋契約與供應商 system prompt 的定期逐條稽核。
