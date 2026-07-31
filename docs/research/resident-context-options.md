# 常駐 context：現況盤點與槓桿

[← 回研究摘要入口](README.md)

這份記錄**選項與其證據狀態**，不是規範。規範（判定表、預算紀律、驗收流程）在
[contract-slimming.md](../contract-slimming.md)。

**判準沿用規範原則 1：「刪掉會不會讓模型犯錯」。** 本文的每一條槓桿都以那個問題的
答案排序，不以能省多少字排序。字數是規則密度的代理指標，不是目的——所以下面每一條
的第一欄是**證據狀態**，字數只是附註。

## 先把尺度講清楚

只看常駐層自己，很容易把小數字看成大數字。實測對照（`usage-report --days 7`，本機）：

| | 值 |
|---|---|
| main opus-5 每回合 prompt context | p50 **24.4%**、p95 **75.1%**（1M window）|
| 整個常駐層 | 992 words ≈ 1.5–2K tokens（由 bytes 推估）|
| 常駐層佔實際 prompt | **0.82%**（p50）／ **0.27%**（p95）|
| 修掉 56 words 佔實際 prompt | **0.049%**（p50）／ **0.016%**（p95）|

**所以：常駐字數不是目前 context 壓力的來源。** p95 的 75.1% 來自 transcript 累積、
工具輸出與檔案讀取，跟這 992 words 幾乎無關。任何以「省 token」為理由的常駐修剪，
報酬都在雜訊裡。

這**不推翻**規範原則 2。IFScale 量的是指令**條數**增加時的遵循衰退，Context Rot 量的是
context 變長時的可靠性下滑；原則 2 講的是規則彼此稀釋注意力，不是 token 佔比。預算作為
「規則密度的棘輪」仍然有效——失效的只是「省下的字數」這個報酬敘事。

## 現況（2026-07-31 實測）

來源 `scripts/prompt-surface-census.py`；上限來源 `test_contracts.py`。

| | 契約 | skill metadata | 常駐合計 | 餘裕 |
|---|---|---|---|---|
| Claude | 397 / 520 | 595 / 620 | 992 / 1140 | 148 |
| Codex | 527 / 540 | 515 / 540 | 1042 / 1080 | **38** |

（Codex 契約 2026-07-31 曾降為 480，經 re-review 全部還原；L4 淨變動為零。）

skill metadata 逐項（兩側共用的描述逐字相同）：

| skill | words | 備註 |
|---|---|---|
| `speak-human-tw` | 176 | 單項上限 180，只剩 4 words。雙語各述一次，因為它是唯一會被使用者以任一語言直接叫用的 skill |
| `task-observer` | 102 | |
| `headroom-protocol` | 92 | |
| `baton-dispatch` | 88 | Claude 專有 |
| `leaf-dispatch` | 77 | Codex 專有，合併了 Claude 側兩支的 territory |
| `provider-routing` | 69 | Claude 專有 |
| `experience-ledger` | 68 | |

Codex 側餘裕 38 words（約半支 skill 的描述）是這份盤點的直接動機——但**餘裕變少不等於
該砍**，見下一節。

## 六個可能結果，不是五個槓桿

預算逼近上限時，正確結論有六種，砍只是其中之一：

| # | 結果 | 什麼情況下是對的 | 證據狀態 |
|---|---|---|---|
| L1 | 修剪 description | 該子句刪掉不會讓模型犯錯 | **未證實**——s10 arm B/C 通過是弱證據 |
| L2 | 稽核兩份契約的落差 | 那 130 words 有一部分刪掉不影響 Codex | **未解**——曾以為 47 words 是 L4 材料，實測推翻 |
| L3 | 分層移出（→ skill／hook／role） | 內容不是每 session 必要 | 規範既有第一手段，已大量套用 |
| L4 | 刪除供應商已保證的行為 | 重述 = 純注意力稅 | **Codex 側已跑，淨變動 0**；Claude 側缺證據 |
| L5 | 抑制新增 | 新規則推得出來 | 已有機制（新 skill 未登錄即測試失敗）|
| **L6** | **調高預算** | **每一句都通過原則 1** | 規範明文允許（需理由寫進 commit）|

**L6 不是失敗選項。** 如果 1042 words 每一句都是「刪掉會讓模型犯錯」，那正確答案就是
調高上限並記明理由——尤其在字數對真實 prompt 的影響只有 0.27% 的前提下。把 L6 漏掉會
讓讀者只往下砍，這正是本文第一版犯的錯。

### L1 · description 修剪

`speak-human-tw` 176 words，是中位數的兩倍，也是唯一逼近單項上限的。
s10-skill-recall 四臂實測（2026-07-31）：砍文件類型列舉（B）或砍不觸發排除項（C）
單獨做，鑑別度無損；**兩個都砍（D）精確度立刻崩**，3 樣本中 1 次把 nginx 設定檔／
error log／Python 程式碼全導向 `speak-human-tw`。

那 176 words 因此有一部分是**冗餘覆蓋**：兩條子句互相補位。

但 s10 量的是**鑑別度**（批次分類），不是實際載入行為，證據不對稱：失敗是強證據，
通過是弱證據。所以 B／C 的乾淨結果**不構成修剪許可**，只證明「不是明顯壞的修剪」。

### L2 · 兩份契約的落差

契約本體 Claude 397 vs Codex 527，差 130 words。規範原則 5 要求「語意同步、字面各自
最短」，但目前只有子句層級的存在性斷言，沒有全文 twin 綁定，所以這個落差**沒被檢驗過
是否正當**。

**它不是純浪費。** Codex 把 dispatch／routing 合併成單一 `leaf-dispatch`(77)，Claude 是
`baton-dispatch`(88) + `provider-routing`(69) = 157。Codex 少花 80 words 在 skill 層，
很可能有一部分挪進了契約。兩側常駐總計 992 vs 1042 只差 50，這比「Codex 契約肥了 130」
接近事實。

可查的是：那 130 words 裡哪些**刪掉會讓 Codex 犯錯**。這需要一次人工逐條對照，
不需要任何新設施——但**做完之後結論可能是 L6**，不要預設是 L2 執行。

### L4 · 供應商重述稽核（Codex 側已執行 2026-07-31）

**證據來源**：Codex 把自己的 base instructions 寫進每個 rollout 的
`session_meta.base_instructions`（`~/.codex/sessions/**/rollout-*.jsonl`），所以 host prompt
可以**逐字讀取**而不是推測。管道乾淨——六個契約專屬字串在其中全為 0，無循環引用。

**結果：稽核刪了三條，re-review 全部還原。淨變動為零，留下的是方法規則。**

第一次只讀了**一份** rollout 就下結論。實際上 91 份本機 rollout 有**八種不同的 host
prompt**，而我讀到的那份是唯一同時含〈File editing constraints〉與〈Destructive Actions〉
兩段的變體——**對減法決策而言是最糟的取樣**，它讓供應商涵蓋看起來最大。

分裂軸是 **session 類型**，不是 CLI 版本。cli ≥ 0.145.0：

| kind | n | autonomy | no-ask-scoped | dirty-worktree |
|---|---|---|---|---|
| top-level | 3 | 3/3 | 3/3 | 3/3 |
| **subagent** | **47** | **0/47** | **0/47** | **0/47** |

而契約**確實送進 subagent**：rollout 裡它是 `role: user`、開頭 `# AGENTS.md instructions`
的 `<INSTRUCTIONS>` 區塊，並鏡射在 `world_state.agents_md`。所以 subagent prompt 沒有的
條款，沒有第二個來源。刪掉它們等於讓**目前每一個 subagent session**——會寫檔的那一半——
失去「使用者未提交的工作屬於使用者，要保留」這句話的唯一出處。

**得到的規則**：減法必須對照**任何會載入該契約的 session 中最薄的 prompt 變體**，
不是抽樣到的那一個。已寫進 `CodexContractRestatementTests` 的 docstring 與實際斷言。

**上表可重跑**，不必重建分析：

```bash
scripts/codex-prompt-census.py --min-cli 0.145
```

它同時做循環性檢查（我們自己的契約字串若出現在 host prompt 裡就警告）。刻意沒有
`--check` 模式——輸入是 machine-local 且本來就會變，釘住快照只會讓非作者的人一律失敗。
它是給人看的證據，不是 gate。`test_the_vendor_census_covers_every_justified_clause`
確保「以供應商涵蓋為由保留或刪除的每一條款」都是這支腳本的一個欄位。

**唯一真正的重述**：外部寫入／破壞性動作的授權句——〈Destructive Actions〉在 subagent
側確實有（73/77）。但仍保留，因為兩個失效方向不對稱：供應商若移除該段，過度謹慎可回復，
未經授權做破壞性動作不可回復。為 ~35 words 承擔那種形狀的尾部風險不划算。

**未動**：語言規定、orchestration 整段、`narrowest verification that could refute`、
`DECISION:`／`[UNCERTAIN:]`、RTK——Codex host prompt 沒有 subagent／派工概念，也沒有語言
規定，這些是加值而非重述。

### L4 · Claude 側：無法執行

**Claude Code 不記錄自己的 system prompt**（transcript 的 record types 裡沒有任何一種
承載它）。唯一來源是執行中 session 的 context，而那份**混合了供應商固定文字與本機注入**，
無法可靠分離，且 n=1。

所以 L4 在兩個 provider 上的可稽核性不對等：**Codex 可重複執行，Claude 不行。**
要補上，需要一個等價於 rollout `base_instructions` 的擷取管道。在那之前，Claude 契約的
既有 5 條禁述清單（`test_claude_md_does_not_restate_the_harness_system_prompt`）維持不變，
但要知道它的證據基礎比 Codex 側弱。

## 目前的建議

**沒有任何一條槓桿有「刪掉會讓模型犯錯」的反證，所以沒有一條該現在動。** L4 已執行完畢，
結果是淨變動零——它買到的不是字數，是那條「對照最薄變體」的方法規則，以及一次證實：
在這種尺度下（見開頭的 0.049%），減法出錯的代價遠大於減法成功的收益。

L2 的 130-word 落差仍未解。曾以為其中 47 是 Codex 重述自己的 host prompt，實測推翻。
要查就要用原則 1 的問題去查，不是用字數去查。

## 延後項：runtime-selection eval

**定位（本文第一版寫錯，此處為更正）**：它**不是**缺失的能力，而是既有人工路徑的
**便宜替代品**。下修預算的證據路徑一直存在——`contract-slimming.md` 的驗收段有兩條：
真實任務回歸，以及「無失敗 trap 的規則是刪除候選」。它們昂貴且未自動化，但存在。

runtime eval 想買的是把 L1 的「通過」從弱證據變成強證據，而不必每次都跑 3–5 個真實任務。

**形狀**：丟單一開場訊息進 fresh session，觀測它自己載了什麼，答案表沿用 s10 的
`ANSWERS`：

```
claude -p "<utterance>" --settings <scratch>/settings.json
       --output-format stream-json --max-turns N
  在只裝了受測描述的 scratch HOME 底下
→ 從事件流撈 Skill tool_use 的 skill 名稱
```

**可行性已確認**（2026-07-31 實測）：每次 skill 載入都是一個 `Skill` tool_use，帶
`input.skill` = skill 名稱，寫進 transcript；`PreToolUse` 也支援 `Skill` matcher。

### 為何延後

1. **沉默會被讀成通過。** 十八題有七題答案是 `none`，即斷言「沒有發生」。session 當掉、
   反問、逾時全都沒有 `Skill` 事件，全部記成正確——**崩得越徹底，成績單越漂亮**。
2. **沒有 fixture hash 的等價物。** s10 的 fixture 用 SHA-256 綁在 live frontmatter 上。
   runtime eval 的輸入是**整個執行環境**（CLI 版本、settings、hook 集合、系統提示組裝、
   模型版本），沒有一項綁得住。三個月後的數字不可比，**而且不會出聲**。
3. 報酬本身很小：見開頭的尺度表。
4. 噪音：arm D 訊號是 1/3，live session 變異更大，3 樣本分不開。

第 1、2 點是同一類：**會說謊的 gate 比沒有 gate 糟**，而兩者都朝「安靜地通過」壞。
這是延後的主因，成本不是。

### 真要做時

**先解存活判準，再寫其他任何東西**（設計筆記在 s10 的 `GROUND-TRUTH.md`）。一個 session
必須證明自己做了實質工作，它的「沒載入」才有資格算數。grader 最後再寫，它最簡單。

規模：批次 trap 當**篩選**，runtime 當**確認**，只跑打算出貨的那一個修剪、control +
該臂、只跑關鍵題 = 8 題 × 3 樣本 × 2 臂 = 48 session。

## 重新檢視的觸發條件

以**效果訊號**為主，字數門檻只作為次要提示：

- 某條常駐鐵律開始在真實任務中被遺漏（驗收流程會看到）
- routing 開始誤觸或漏觸（s10 或真實任務中出現）
- L4 稽核發現契約與供應商 system prompt 有牴觸——那是 bug，優先於任何字數考量
- 需要新增常駐 skill 而無處可讓：此時先問 L6，再問 L1–L4
- 出現不需要 live session 就能量鑑別度的方法（例如供應商公開 skill 選取的機率輸出）
