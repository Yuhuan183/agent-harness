# 常駐指令與供應商指引

[← 回研究摘要入口](README.md)

## 這份文件回答什麼

三個問題, 由外而內:

| 問題 | 在哪一節 | 一句話答案 |
|---|---|---|
| 常駐指令為什麼要瘦 | 常駐指令與 context | 規則會互相搶注意力, context 大不等於能無損用完 |
| 現在到底佔了多少 | 實際量測與操作分級 | 有本機基準快照與四段操作分級, 但那是專案啟發式, 不是供應商公布的故障線 |
| 兩家官方怎麼說 | 供應商官方指引 | 都升級成帶數字的官方立場, 但數字都是**供應商自評** |
| 有沒有我們沒寫的常駐內容 | 供應商注入的常駐段落 | 有一塊只長在 Opus 5 上, 位置比契約靠後, 而且沒有 opt-out |

前三節收斂成同一條維運規則: **加規則前先找矛盾**. 肥大有預算擋得住, 矛盾沒有.
第四節是這條規則的反面: 那個矛盾是別人寫進來的, 我們既看不見, 也刪不掉.

## 常駐指令與 context

**已驗證**

- Anthropic Claude Code Best Practices 建議用一個問題判斷內容去留:「刪掉它會不會讓 Claude
  犯錯」; 並警告肥大的 `CLAUDE.md` 會讓重要指令被淹沒.
  <https://code.claude.com/docs/en/best-practices>
- IFScale (arXiv 2507.11538) 研究長指令集合下遵循度怎麼衰退; 它能佐證「規則會互相搶注意力」,
  但單靠它證不出任何固定的行數上限. <https://arxiv.org/abs/2507.11538>
- Chroma Context Rot 顯示模型的可靠性可能隨 context 變長而非線性下滑; context window 大,
  不代表能無損用完裡面的每一段. <https://research.trychroma.com/context-rot>
- Agent Skills 把「按需載入的內容」和「常駐的 metadata」分開, 適合承載那些不必每回合都載入的
  流程. <https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills>

**推論**: 本 repo 用短主契約, 自足的 leaf role, skills/docs 分流, 以及 hooks/tests 強制,
方向和上面這些證據一致.

**啟發式**: `CLAUDE.md`/`AGENTS.md` 目標抓 40–80 行, context 明顯膨脹時就在收斂點壓縮.
這是維運預算, 不是已被證明的通用臨界值; 要不要調, 看真實任務回歸的結果.

## 實際量測與操作分級 (2026-07-28)

**已驗證的容量**: 目前
[Claude Fable 5, Opus 5, Sonnet 5 與 Opus 4.8](https://platform.claude.com/docs/en/about-claude/models/overview)
官方 context window 都是 1M tokens; Codex 使用的
[GPT-5.6 Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol) 官方 context window 是 1,050,000 tokens
(最大 input 922,000, 最大 output 128,000). 容量只是硬上限, 不代表接近上限時仍能無損
保留每條規則的注意力.

本 repo 現在提供兩種不同但同口徑的診斷:

```bash
# Claude: 最近 7 天每回合 prompt-context P50/P95, 並列出壓力最高的 sessions
~/.claude/scripts/usage-report --days 7 --by-session --top 20

# Codex: 最近一回合實際佔用, 剩餘 context, 以及帳號 quota
~/.codex/skills/experience-ledger/scripts/codex-usage
```

| 佔用 | 分級 | 操作 |
|---:|---|---|
| `<30%` | low | 不需額外動作 |
| `30–<50%` | watch | 保持單一主題, 階段邊界留下 checkpoint |
| `50–<65%` | checkpoint | 換階段前先收斂, 避免再灌入無關大型輸出 |
| `>=65%` | compact | 關鍵判斷前 compact, 或從 checkpoint 開新 session |

這組數字是**專案操作啟發式**, 不是供應商公布的故障線. 它刻意在硬上限前預警, 理由是上面的
context-rot 證據與本專案的多層契約形狀; 後續應拿 P95 與返工/漏規則案例一起校準.

**口徑邊界**:

- Claude transcript 沒有直接寫「本回合已占 window 幾成」; 報表以該 assistant turn 的
  `input_tokens + cache_creation_input_tokens + cache_read_input_tokens` 當 prompt-context
  代理值, 輸出 P50/P95. 未知舊模型先用保守的 200k; 已知實際容量時用
  `--context-window` 覆寫.
- Codex rollout 已提供 `last_token_usage.total_tokens` 與 `model_context_window`, 所以用兩者
  算最近一回合佔用. `total_token_usage` 是整個 session 累計消耗, 只能看成本, 不能拿來當
  當前 context occupancy.
- account quota (例如 5h/weekly window) 是能不能繼續呼叫的限制; attention pressure 是
  單次判斷是否可能被長 context 稀釋. 兩者都要看, 但不能互相替代.

**本機基準快照 (2026-07-28, 最近 7 天)**:

| 路徑 | P50 | P95 | 判讀 |
|---|---:|---:|---|
| Claude main/Fable 5 | 22.8% | 51.9% | 一般回合不高, 但長 session 已進 checkpoint 區 |
| Claude main/Opus 5 | 28.9% | 86.0% | 尾端明顯過長, 關鍵判斷前應 compact/換 session |
| Claude subagent/Opus 5 | 12.8% | 19.8% | leaf context 保持在低區, context protection 有實際差異 |
| Claude subagent/Sonnet 5 | 4.8% | 11.6% | leaf context 低 |

同一時間的 Codex rollout 回報有效 `model_context_window=258,400`, 最近一回合約
59.2k/22.9%, 屬 low; 整個 session 累計約 56.0M tokens, 證明累計量若誤當佔用會得出完全
錯誤的警報. 這個 258,400 是**當下 Codex runtime 的實際限制**, 操作判斷優先於上面
GPT-5.6 Sol API 頁面的產品容量; snapshot 會隨 runtime, 模型與 session 更新, 應以指令重查.

## 供應商官方指引 (2026-07)

同一週裡, 兩家把「常駐指令要瘦」從社群經驗法則升級成帶數字的官方立場. 兩份都是**一手來源**,
但數字都是**供應商自評**: 沒有公開 harness, 題目和計分細節, 所以等級是「已驗證的官方主張」,
不是能獨立重跑的實驗.

先看兩家並排:

| | Anthropic (2026-07-24) | OpenAI (讀取 2026-07-26) |
|---|---|---|
| 官方數字 | Claude Code system prompt 刪掉 **80% 以上**, coding evaluations **量不到損失** | 精簡 system prompt 讓評分升約 **10–15%**, 總 token 降 **41–66%**, 成本降 **33–67%** |
| 適用世代 | Opus 5 / Fable 5 等 Claude 5 世代 | GPT-5.6 |
| 自己標注的限制 | 未公開 harness, 題目, 計分 | 同左, 且官方註明是方向性區間, 要自己驗 |
| 對本 repo 的**新增**規則 | 矛盾成本; 記憶層分工 | 矛盾比缺漏貴; 不要重複「先問過再動」; verbosity 要指名; effort 階梯定位 |

兩邊各自的細節在下面兩小節. 兩份**同時**點名的那一項 - 矛盾 - 是本次唯一真正新增的失敗形態.

### Anthropic: Claude 5 世代的 context engineering (2026-07-24)

<https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models>

**官方數字**: 為 Opus 5/Fable 5 等 Claude 5 世代模型, 把 Claude Code system prompt 刪掉
**80% 以上**, coding evaluations **量不到損失**.

文章列出的「昔非今是」對照本 repo:

| 舊做法 → 新做法 | 本 repo 現況 |
|---|---|
| 給規則 → 讓模型用判斷 | 已對齊 (短契約, 判準「刪掉會不會犯錯」); 本次補上**矛盾**這個獨立的失敗形態 |
| 給範例 → 設計介面 (漸進揭露, 工具 deferred loading/`ToolSearch`) | 已對齊 (skills+`references/`; 本 session 就是用 ToolSearch 載入工具) |
| 到處重複 → 工具用法寫進工具描述 | **部分做不到**: 本 repo 只 deploy 全域契約, 改不了供應商的工具描述; RTK/Headroom 因此各留一行觸發句 |
| CLAUDE.md 當記憶 → CLI 自動記憶 | **新增分工**: 記憶層寫進 playbook 的分工表, 常駐契約不再扛「怕忘記」 |
| 簡單 spec → 豐富參照 (code, 測試套件當 spec, rubric+dynamic workflow) | 已有等價實作: trap fixture+機械 grader 就是「測試當 spec」與 rubric; 本次把「brief 指向 grader 勝過複述判準」寫成規則 |

文章對 CLAUDE.md 的具體建議: 保持輕量, 把 token 花在**程式庫的陷阱**上, **不要寫模型翻一下
repo 就知道的事**, 多用漸進揭露. 對 skills 的建議: 當它是輕量指南, 不是緊箍咒, 除非那個領域
確實高風險. 另外提供 `claude doctor`/`/doctor` 自動評估 skills 和 CLAUDE.md 的肥瘦.

其中「不要寫可推斷的事」和「skill 不要過度約束」本 repo 早就成文; 真正**新增**的是矛盾成本
(見下) 和記憶層的分工. 文章舉的失敗例子, 正是本 repo 的風險形狀: 同一次請求裡, 一邊寫
「文件留得合宜」, 另一邊寫「不要加註解」.

**2026-07-26 稽核結果 (已驗證)**: 拿當期 Claude Code system prompt 逐條比對
`CLAUDE.contract.md` 的五條 working agreement 和三條 main-only 條款, **沒牴觸, 沒重述**.
重述早在 52b434b 就清掉了. 剩下的每一條 — 繁中回覆, `DECISION:` 標記, 最窄驗證, 保留 dirty
worktree, 派工剎車 — system prompt 都沒有涵蓋.

所以這次整合**不動常駐契約**, 落點是
[契約瘦身規範](../contract-slimming.md) 的原則 2b 和內容判定表: 管的是**下一次**改契約時的
判準, 不是現在多加幾句. 這本身就是文章的建議: 先找矛盾, 找不到就別動.

### OpenAI: GPT-5.6 model guidance (讀取 2026-07-26)

<https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.6#prompting-best-practices>

**官方數字**: 在內部 coding-agent eval 上, 精簡 system prompt 讓評分升約 **10–15%**,
總 token 降 **41–66%**, 成本降 **33–67%** (官方註明是方向性區間, 要自己驗).

對本 repo 直接有後果的四條:

1. **矛盾比缺漏貴.** GPT-5.6 嚴格遵守 prompt contract, 碰到互相衝突的規則會花 reasoning
   token 去調和, 而不是擇一, 結果更慢, 更貴, 更常錯. 這和 Anthropic 那篇的實例互相佐證,
   已寫進 playbook §1 和契約瘦身規範.
2. **不要重複「先問過再動」.** 官方點名: 重複這類話會對安全, 預期內的動作觸發多餘的
   確認請求; 正解是明確列出安全的本地動作, 政策只放一處, 每條只講一次.
   `AGENTS.contract.md` 第 8–9 行已經是這個形狀 (先列出免授權的安全動作, 再把授權邊界
   `stated once here`). **2026-07-26 逐檔稽核結論: 無違反.**

   唯一看起來像重複的, 是 AUTH 條款在 `executor`/`mech-executor`/`security-executor`
   三個 role TOML 各出現一次. 但那是三份**自足, 互斥載入**的角色契約: 一個 leaf 永遠
   只看到其中一份, 不算官方所指的「同一個 prompt 內重複」. 記在這裡, 免得日後有人
   當它冗餘刪掉, 拆掉自足性.
3. **`text.verbosity` 與「盡量簡短」.** GPT-5.6 預設就比 5.5 精簡, 籠統的簡短指令可能多餘,
   甚至讓回覆過短; 要留就得指名保留什麼, 捨棄什麼. 兩份契約現行的
   「Lead with the outcome. Keep conversation proportional and requested artifacts complete.」
   已經是這個形狀 (同時指名保留什麼, 可壓縮什麼), 不必改寫; 規則本身已反映到 playbook §4.
4. **effort 階梯的官方定位**: `medium` 是平衡起點, `low` 給延遲敏感, `high`/`xhigh` 只在
   量得到品質增益時用, `max` 留給最難的品質優先工作, 而且該跟 `xhigh` 對比, 別預設它更好.
   本 repo 的三個 profile 本來就沒有任何角色釘到 `high` 以上, 方向一致; 已記入
   `main/codex/model-routing.toml` 的 `model_guidance_source`.

**刻意沒做的事**: Programmatic Tool Calling, multi-agent [beta], `reasoning.mode: "pro"`,
explicit prompt caching 和 `reasoning.context` 都是 Responses API 的能力. 本 bundle 透過
Codex CLI 派工, 這些參數不在可控面上, 所以只記錄, 不接線; `none` effort 同理 (見
[2026-07-26 AA 節](model-evidence.md#artificial-analysis-重新取數-完整-effort-階梯-2026-07-26)
結論 4).

**共同結論 (推論)**: 兩家的建議在本 repo 收斂成同一條維運規則 — **加規則前先找矛盾**.
本 repo 現有的預算機制 (`word_count` 上限) 只擋得住肥大, 擋不住矛盾; 矛盾要靠
「同一政策只有一個真相源」+twin-parity 測試+契約與供應商 system prompt 的定期逐條稽核.

## 場域研究: 常駐檔到底買到什麼 (2026-08-08)

前兩節是供應商說什麼. 這節是別人量出什麼, 而且第一次量到本 repo 賴以立論的那件事.

| 來源 | 量的是哪一種常駐內容 | 結果 |
|---|---|---|
| [arXiv 2607.27250](https://arxiv.org/abs/2607.27250) (2026-07-28) | **知識型**: repo 事實寫進 `AGENTS.md`. 兩個 frontier agent (Claude Code, Codex), 3 個真實 repo, 17 個任務, 288 次評分執行, 只變 context 注入策略 | 正確率無可測增益, 等價檢定把效果界在 <=10-15pp. 失敗來自實作能力 (功能設計, 模式選擇, 接線), 不是缺 repo 知識; 把真正的 `AGENTS.md` 注回去「從未把差一點的失敗救成通過」 |
| 本機 s7 A/B (2026-07-23) | **程序型**: 一句機器可檢的 gate 子句 | exact-template 合規 1/4 -> 3/3 (bridge), 6/10 -> 3/3 (opus) |
| [arXiv 2604.14228](https://arxiv.org/abs/2604.14228) | 常駐檔的**進場位置**: Claude Code v2.1.88 原始碼層拆解 (第三方逆向) <!-- pinned 2026-08-21 --> | `CLAUDE.md` 以 user context 進場, 不是 system prompt; 服從因此是機率性的 |

前兩列結論相反卻不矛盾 - **量的不是同一種子句**. 合起來給出一條本 repo 之前沒有的判定軸: 常駐層的每一句先分清是**程序/權限**還是 **repo 知識**. 前者維持現行預算與「無 failing trap, 無規則」公約; 後者現在有外部有界證據說它買不到正確率, 預設可砍, 要留就得自帶本機反例.

第三列改的是宣稱強度而不是內容: 常駐層拿不到強制力, 只拿得到權重. 這與上游 v1.3.9 撤下「自動派工」宣稱是同一件事, 展開見 [peer-harnesses.md](peer-harnesses.md).

壓縮方向另有一個外部命名: [ACE](https://arxiv.org/abs/2510.04618) (ICLR 2026) 把「反覆為了簡短而重寫會侵蝕細節」定名為 brevity bias 與 context collapse, 對策是逐項增量更新而非整段重寫. `scripts/contract-operator-delta.py` 已經是那個形狀, 這份研究只補一個外部理由. **不採用**它的自動 Curator: 常駐層要人審與 Git 部署, 而「通過全部斷言仍帶進十二個語意缺陷」是記錄在案的相關失效.

同一批重查還有一條與常駐內容無關, 但落在規則生命週期的另一端: **被擋下來之後要回什麼**. Anthropic 的 [auto mode](https://www.anthropic.com/engineering/claude-code-auto-mode) 用 deny-and-continue - 拒絕當成 tool result 送回並要求改走安全路徑, 代價是一次重試而不是一個死掉的 session, 並在連續 3 次或累計 20 次拒絕時升級給人; Deep Agents CLI 0.1.52 把 HITL 拒絕理由改寫成給模型看的形式, 是同一做法的第二個實作. 同一篇另給兩個本 repo 用得上的判斷: 閘的分類器**刻意不讀**模型自己的散文與工具輸出 (讀了會被說服, 也會被注入), 以及它的殘留失效是「找到形狀像核准的證據, 卻沒確認那份核准涵蓋這次動作的影響範圍」- 後者正是本 repo `AUTH:` 那條 gate 擋的東西, 獨立來源撞上同一個失效.

- [UNCERTAIN: 2607.27250 只有 2 個 agent, 3 個 repo, 17 個任務, 作者自述這題的證據基礎本身矛盾, 且報的是效果**上界**而非零效果. 當先驗用, 不當結論用.]
- [已知假陽性, 不要追: `scripts/evidence-check.py` 會把上表的 `v2.1.88` 報成一筆版本差異 (本機是 2.1.226). 那個版號是**那篇逆向分析的對象**, 不是對本機的查核宣稱, 所以它本來就不該跟著本機版本走. 工具收緊到「版號緊貼工具名」之後仍抓得到它, 而再收緊會開始漏掉真的宣稱; 留著這一筆已知噪音, 比讓檢查變得抓不到東西好.]
- [UNCERTAIN: 2604.14228 是釘在 client v2.1.88 的第三方逆向, 不是供應商陳述, client 改版即可能失效. 本機另有可觀察佐證 (見[研究摘要方向 1](README.md#待辦方向)), 但那是單一實例.]

## 供應商注入的常駐段落: `heron_brook` 只長在 Opus 5 上 (2026-08-28)

前面幾節問的都是「我們自己該寫多少」. 這節問第五個問題: **有沒有一段常駐內容不是我們寫的, 我們也刪不掉**. 有. 它在 prompt 裡的位置比契約更靠後, 而且整份 model catalog 裡只有 `claude-opus-5` 拿得到它.

線索是 [anthropics/claude-code#80988](https://github.com/anthropics/claude-code/issues/80988) (2026-07-24 開, 32 則留言, 全部來自非官方帳號, 至 08-26 無官方回覆也無標籤). 那串的取證停在 client 2.1.245, 所以只當先驗; 下面每一條都在本機 **2.1.247** 重跑過.

### 那段文字與它的閘 (已驗證, 本機 2.1.247)

Claude Code 的 system prompt 由具名區塊組成. 其中一塊註冊名是 `heron_brook`, 硬編碼的預設內容是兩行:

```
Do not call the AgentTool unless the user requested it
Do not use workflows or deep-research unless the user requested it
```

它分三層解析, 前兩層都來自伺服器, **只有第三層受 killswitch 保護**:

```js
function RUs(e){
  let t=Ag()?.tengu_heron_brook;                 // 1. client_data 推的字串
  if(typeof t==="string"&&t.trim()!=="") ...     //    直接用, 不看模型也不看 killswitch
  let n=we("tengu_heron_brook","");              // 2. GrowthBook 字串旗標, 同上
  if(n.trim()!=="") ...
  if(Eqt(e)) return aqr;                         // 3. 硬編碼 fallback, 受能力閘
  return null
}
```

能力閘 (`Eqt`, 與五個姊妹區塊共用的 `mf` 同形) 要兩個條件同時成立: 模型帶 `opus_5_prompt_bundle` 能力, 且 `tengu_fennel_godwit` 為 false. 前者在 binary 內建的 model catalog 裡逐一查過, **17 個模型只有一個帶**:

| 帶 `opus_5_prompt_bundle` | 不帶 |
|---|---|
| `claude-opus-5` | 其餘 16 個, 含 `claude-opus-4-8`, `claude-sonnet-5`, `claude-fable-5`, `claude-mythos-5` 與全部 4.x 世代 |

本機當下的旗標狀態讓第三層直接生效: `~/.claude.json` 的 `cachedGrowthBookFeatures` 共 557 個鍵, 其中 `tengu_fennel_godwit` 是 `false` (killswitch 關著), `tengu_heron_brook` 根本沒被 cache (伺服器沒推字串, 所以走 fallback). 對照組是這份文件被寫出來的那個 session 本身: main 模型 `claude-opus-5[1m]`, 那兩行**逐字出現在它的 system prompt 裡**.

可重跑, 而且不再靠人記得跑: 上面三件事 (catalog 裡誰帶這個能力, 出廠字串還在不在, 兩個旗標現在是什麼值)
已經收進 [`prompt-bundle-report`](../../main/claude/scripts/prompt-bundle-report), 部署後在
`~/.claude/scripts/`:

```bash
~/.claude/scripts/prompt-bundle-report          # 人看的
~/.claude/scripts/prompt-bundle-report --json   # 機器看的
```

它把每次觀測寫進 `~/.claude/telemetry/.prompt-bundle-state.json`, 只在**與上次不同**時 exit 1;
`weekly-integrity` 每七天跑一次並把 exit 1 當 finding. 這是刻意的取捨 —— 穩態早就寫在這一節裡,
每週重講一次只會訓練讀者跳過它. 它關不掉任何東西, 只回答「現在是什麼狀態, 跟上次一不一樣」.

### 為什麼契約攔不住它

區塊組裝順序在同一份 binary 裡讀得到, 那兩件事在裡面是分開的兩層:

```js
...ku(`memory${a}`, ...), ku("env_info_simple", ...), ku("language", ...), ku("output_style", ...),
   ku("context_management", ...), ku("brief", ...), ku("act_dont_rederive", ...),
   ku("delivering_work_max", ...), ku("overcorrection", ...), ku("subagent_steer_delegation", ...),
   ku("heron_brook", ...), ku("willow_tern", ...), ku("autonomy_append", ...), ku("endconv_deferred_hint", ...)
```

`heron_brook` 落在整串的尾端. 而本 session 的直接觀察是: **契約內容根本不在這條 system prompt 鏈上** — `CLAUDE.contract.md` 的正文是以 `# claudeMd` 之名, 包在第一個 user turn 的 `<system-reminder>` 裡進場的. 這正好是 2604.14228 那條 UNCERTAIN 所宣稱的形狀, 在 2.1.247 上仍然成立, 而且說明了本 repo 自己 2026-08-14 那批 replay 為什麼會那樣: 四條規則各配一句正面矛盾的 `--append-system-prompt`, **派工預設那條 (`p4`) 注入勝 5/5** (見 [landing-log](landing-log.md#2026-08-14-方向-1-的推翻條件成立--契約有時候真的贏)). 同一個位置關係, 同一個方向, 只是這次寫那句話的不是我們.

### 沒有可用的 opt-out (已驗證)

- **`heron_brook` 沒有任何環境變數.** 姊妹區塊共用的 `gt(e,t,n){return e||mf(n)||...}` 第一個參數就是 env var (`CLAUDE_CODE_GAULT_KESTREL`, `CLAUDE_CODE_GORSE_PLOVER`, `CLAUDE_CODE_ACT_DONT_REDERIVE` 等), 但 `RUs` 直接呼叫 `Eqt`, 繞過那個 helper. 順帶一個對 issue 串的修正: 那些 env var 是 `e ||`, 只能**強制打開**, 本來就不是關閉開關.
- **`CLAUDE_INTERNAL_FC_OVERRIDES` 是死碼.** 2.1.247 的 `getEnvironmentOverrides()` 第二行就 `return this.environmentOverridesParsed=!0,this.environmentOverrides;`, 讀 env 的那行在它下面, 永遠到不了.
- **`--exclude-dynamic-system-prompt-sections` 反向.** 從組裝碼看, `excludeDynamicSections` 只影響 `memory`, `env_info`, `scratchpad` 三塊; 打開它是把記憶搬走, `heron_brook` 原地不動.
- **killswitch 不是我們能碰的, 而且太寬.** `tengu_fennel_godwit` 同時管 `delivering_work_max`, `overcorrection`, `act_dont_rederive` 等五個姊妹區塊, 就算翻得動也是為了兩行賠掉五塊; 何況前兩層根本不看它.
- 手改 `~/.claude.json` 的 `cachedGrowthBookFeatures` 無效, 那是啟動時會被伺服器覆寫的快取, 不是設定 (issue 串 08-26 的量測; 本機未重跑).

### 對本專案的三個後果

1. **受威脅的不是「派工變少」, 是那三個非選配的角色.** 本 repo 的契約本來就是 direct execution 為預設, 方向與這兩行一致. 真正的傷害在 `verifier` / `plan-verifier` / `security-reviewer` — 它們存在的理由是 fresh-context independence, 不是省時間. issue 串裡最一致的一條觀察是: 這段文字**擋不住規定性指令, 但打得贏裁量性指令**, 而本 repo 的 verifier 觸發條件寫在 `provider-routing` 裡, 形狀正是裁量性的. 更難察覺的是零 verifier 在本 repo 看起來完全正常 — 契約自己就寫「至多一個」.
2. **skill 指示的派工不算 user request.** `baton-dispatch` 是決定要派工之後才載入的, `provider-routing` 的 security routing 同理. 由 skill 正文說「dispatch a reviewer」不會滿足 "unless the user requested it", 這是 issue 串裡 skill 作者那則的核心, 而本 repo 整個派工機制都掛在 skill 上.
3. **跨模型比較被污染了.** Opus 5 比其他模型多帶六個 system prompt 區塊, 其中 `delivering_work_max` 與 `overcorrection` 講的正是「把工作做完」與「不要過度自我修正」— 那是 s7 (false completion) 量的東西. 所以 2026-08-04 那批 Opus 5 trap 重跑, 比的是**模型加 prompt bundle**, 不是模型; 見 [model-evidence.md](model-evidence.md) 同日補注.

**誠實邊界**: 以上是機制與位置的取證, 不是效果量測. 本機 `~/.claude/telemetry/delegation.jsonl` 判不了這件事 — 它只記發生過的派工, 不記沒發生的決定, 而 08-10 到 08-16 那段高峰是 replay 批次而非日常工作, 沒有可比的前後基準. issue 串裡有人給了 116 個 session 的前後對照 (Opus 4.8 常態使用 → Opus 5 整週零使用 → 口頭要求後恢復), 但那是別人的機器與別人的契約.

**推翻條件**: (a) 任一路徑出現官方 opt-out (settings key 或 env var), 或 catalog 裡第二個模型帶上 `opus_5_prompt_bundle`; (b) 伺服器改推第一或第二層字串, 屆時上面「文字是那兩行」的部分立刻失效, 只有「有一塊我們控制不了的區塊」還成立. 兩者都靠 `prompt-bundle-report` 當場重查, 不要引用本節的日期; 而 (b) 正是那支腳本被寫出來的理由.
