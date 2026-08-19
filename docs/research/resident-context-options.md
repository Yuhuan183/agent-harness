# 常駐 context: 現況盤點與槓桿

[← 回研究摘要入口](README.md)

這份記錄**選項與其證據狀態**, 不是規範. 規範 (判定表, 預算紀律, 驗收流程) 在
[contract-slimming.md](../contract-slimming.md).

**判準沿用規範原則 1: 「刪掉會不會讓模型犯錯」.** 本文的每一條槓桿都以那個問題的
答案排序, 不以能省多少字排序. 字數是規則密度的代理指標, 不是目的 — 所以下面每一條
的第一欄是**證據狀態**, 字數只是附註.

## 先把尺度講清楚

只看常駐層自己, 很容易把小數字看成大數字. 2026-07-31 以 `usage-report --days 7` 對照過
一次, 結論是數量級的, 所以底下不寫當時的絕對值 —— 那些字數已經變過三次, 而論證沒有:

- main opus-5 每回合的 prompt context 在 1M window 裡是 **p50 約四分之一, p95 約四分之三**;
- 整個常駐層是**四位數的 words**, 換算約 2–3K tokens;
- 兩者相除, 常駐層佔實際 prompt **不到 1%**, p95 時更低;
- 一次典型的修剪 (數十 words) 因此落在**萬分之幾**.

```text
  整個 prompt                       ████████████████████████████████  100%
  └ 常駐層                          ▏                                <1%
    └ 修掉數十 words 的效果          ▏                              ~0.0X%
```

**所以: 常駐字數不是目前 context 壓力的來源.** p95 那三分之二來自 transcript 累積, 工具
輸出與檔案讀取, 跟常駐層幾乎無關. 任何以「省 token」為理由的常駐修剪, 報酬都在雜訊裡.

要當下的絕對值就跑上一節那三支指令; 這裡只保留不隨字數變動的那個比例關係.

這**不推翻**規範原則 2. IFScale 量的是指令**條數**增加時的遵循衰退, Context Rot 量的是
context 變長時的可靠性下滑; 原則 2 講的是規則彼此稀釋注意力, 不是 token 佔比. 預算作為
「規則密度的棘輪」仍然有效 — 失效的只是「省下的字數」這個報酬敘事.

## 現況: 不寫在這裡

**這一節從 2026-08-19 起不複製數字.** 它原本有一張 2026-07-31 的實測表 (契約, skill
metadata, role metadata, 合計, 餘裕), 而三週後每一格都錯了 —— 契約 397 已是 488, skill
metadata 595 已是 917 —— 同時本文下一節寫著 917. 一份標題叫「現況盤點」的文件,
自己跟自己矛盾, 而餘裕欄正是修剪決策的依據.

[契約瘦身](../contract-slimming.md)早就定了這條規矩:「現行數值的唯一真相源是
`test_contracts.py`, 本文不複製數字.」那條當時只寫給它自己. 現在這裡也照辦.

要現況就跑這三支, 各自回答不同的問題:

| 問題 | 指令 |
|---|---|
| 各層量到多少, 上限多少, 還剩多少 | `main/.agents/scripts/python3-run -m unittest discover -s main/claude/tests -k budget` |
| 每一支 skill 與 role 的逐項字數 | `main/.agents/scripts/python3-run scripts/prompt-surface-census.py` |
| 這台機器實際扛多少, 預算蓋到幾成 | `main/.agents/scripts/python3-run scripts/resident-pool-report.py` |

**結構不變, 所以寫在這裡**: 常駐層由三塊組成 —— 兩份契約本體, 每支 skill 的 `name` 與
`description`, 每支 leaf role 的 `name` 與 `description`. 第三塊是 2026-08-01 review 補進
census 的; 在那之前只量 role 本文, 等於把常駐的那一半留在預算之外, 而它同時是這道棘輪
唯一的繞道 —— 把句子從 skill description 搬進 role description, 成本不變而測試全綠.

Codex 側還有一層結構差異: `allow_implicit_invocation: false` 的 skill 不會被注入, 所以它
的 metadata 是 dispatch 成本不是常駐成本. census 從 2026-08-19 起建模這件事, 詳見下一節.

## 但這道棘輪只蓋住六分之一 (2026-08-18 實測)

上面兩張表量的是**本 repo 出貨的部分**. 一個 session 收到的 skill 清單不只這些: 每一支
裝在這台機器上的 skill, 它的 `name` 與 `description` 都列在同一個區塊裡, 成本一樣是每回合付.

| 來源 | skills | words | 佔比 | 有什麼機制在管 |
|---|---:|---:|---:|---|
| 本 repo 出貨 | 9 | 916 | 18.3% | 單項上限 + 每 provider 總量 |
| 本 checkout 的 dev-only | 1 | 119 | 2.4% | 只有單項上限 |
| 其餘 | 40 | 3978 | 79.4% | 沒有 |
| 合計 | 50 | 5013 | | 這是下限, 不是全部 |

來源 [`scripts/resident-pool-report.py`](../../scripts/resident-pool-report.py), 只報不擋.
數字是機器狀態, 會隨安裝的 skill 變動 — 所以看工具的輸出, 不要引用這張表.

2026-08-19 把使用者自撰的 `evidence-ladder` 納管後重量: 第一列 8/787 變 9/916, 第三列
41/4107 變 40/3978, 而**合計一個字都沒動**. 那 129 字本來就在付, 只是棘輪看不見它 — 這一
格量的是**覆蓋率而不是花費**, 兩者一起動只有在真的新增東西的時候 (該次 Codex 側確實多付了
129 字, 因為那一側從來沒有它).

- **為什麼是下限**: CLI 內建的 skill (`artifact-design`, `dataviz`, `code-review` …) 在
  二進位檔裡, 不在磁碟上; plugin skill 在磁碟上, 但「已安裝」與「已啟用」不是同一組, 數
  進去會報出沒有 session 看得到的名字. 兩者都與上表一起列在同一個區塊.
- **為什麼不做成閘**: 那 41 支不是本 repo 的檔案. 一個因為使用者裝了 skill 就擋 commit
  的 hook, 擋的是它沒有立場擋的事. 判準沿用[文件導覽規則 8](../README.md#維護規則): 不是
  這一層付的成本, 就只報不擋.
- **這不推翻上一節的尺度論證, 反而加強它**: 即使是這個放大後的合計, 依那節的口徑仍只佔
  p50 prompt 的個位數百分比. 「省 token」這個報酬敘事還是在雜訊裡.
- **被削弱的是原則 2 那條**: 預算的正當性是「規則密度的棘輪」, 而 session 實際收到的指令
  條目有六分之五不在棘輪內. 最寬的一支 (`lark-apps` 385 words) 是本 repo 單項上限 180 的
  兩倍多. **所以「常駐層受控」讀成「這台機器的常駐注意力受控」是錯的.**
- **推翻條件**: 若量到 skill 描述的條數或字數與模型遵循度有可測關係, 這一節就從「無法管」
  變成「該不該請使用者修剪」. 目前沒有這個證據 (M5 七批 75 次 session 一次都沒量到).

## 六個可能結果, 不是五個槓桿

預算逼近上限時, 正確結論有六種, 砍只是其中之一:

| # | 結果 | 什麼情況下是對的 | 證據狀態 |
|---|---|---|---|
| L1 | 修剪 description | 該子句刪掉不會讓模型犯錯 | **未證實** — s10 arm B/C 通過是弱證據 |
| L2 | 稽核兩份契約的落差 | 那 130 words 有一部分刪掉不影響 Codex | **未解** — 曾以為 47 words 是 L4 材料, 實測推翻 |
| L3 | 分層移出 (→ skill/hook/role) | 內容不是每 session 必要 | 規範既有第一手段, 已大量套用 |
| L4 | 刪除供應商已保證的行為 | 重述 = 純注意力稅 | **Codex 側已跑, 淨變動 0**; Claude 側缺證據 |
| L5 | 抑制新增 | 新規則推得出來 | 已有機制 (新 skill 未登錄即測試失敗)|
| **L6** | **調高預算** | **每一句都通過原則 1** | 規範明文允許 (需理由寫進 commit)|

**L6 不是失敗選項.** 如果常駐層每一句都是「刪掉會讓模型犯錯」, 那正確答案就是調高上限
並記明理由 —— 尤其在字數對真實 prompt 的影響落在萬分之幾的前提下. 把 L6 漏掉會讓讀者
只往下砍, 這正是本文第一版犯的錯.

### L1 · description 修剪

`readable-zh-tw` 是最寬的一支 description, 約中位數的兩倍, 也是唯一逼近單項上限的.
s10-skill-recall 四臂實測 (2026-07-31): 砍文件類型列舉 (B) 或砍不觸發排除項 (C)
單獨做, 鑑別度無損; **兩個都砍 (D) 精確度立刻崩**, 3 樣本中 1 次把 nginx 設定檔/
error log/Python 程式碼全導向 `readable-zh-tw`.

那份描述因此有一部分是**冗餘覆蓋**: 兩條子句互相補位.

但 s10 量的是**鑑別度** (批次分類), 不是實際載入行為, 證據不對稱: 失敗是強證據,
通過是弱證據. 所以 B/C 的乾淨結果**不構成修剪許可**, 只證明「不是明顯壞的修剪」.

### L2 · 兩份契約的落差

契約本體 Claude 397 vs Codex 527, 差 130 words. 規範原則 5 要求「語意同步, 字面各自
最短」, 但目前只有子句層級的存在性斷言, 沒有全文 twin 綁定, 所以這個落差**沒被檢驗過
是否正當**.

**它不是純浪費.** Codex 把 dispatch/routing 合併成單一 `leaf-dispatch`(77), Claude 是
`baton-dispatch`(88) + `provider-routing`(69) = 157. Codex 少花 80 words 在 skill 層,
很可能有一部分挪進了契約. 兩側常駐總計 992 vs 1042 只差 50, 這比「Codex 契約肥了 130」
接近事實.

可查的是: 那 130 words 裡哪些**刪掉會讓 Codex 犯錯**. 這需要一次人工逐條對照,
不需要任何新設施 — 但**做完之後結論可能是 L6**, 不要預設是 L2 執行.

### L4 · 供應商重述稽核 (Codex 側已執行 2026-07-31)

**證據來源**: Codex 把自己的 base instructions 寫進每個 rollout 的
`session_meta.base_instructions` (`~/.codex/sessions/**/rollout-*.jsonl`), 所以 host prompt
可以**逐字讀取**而不是推測. 管道乾淨 — 六個契約專屬字串在其中全為 0, 無循環引用.

**結果: 稽核刪了三條, re-review 全部還原. 淨變動為零, 留下的是方法規則.**

第一次只讀了**一份** rollout 就下結論. 實際上 91 份本機 rollout 有**八種不同的 host
prompt**. 我讀到的那份是唯一同時含〈File editing constraints〉與〈Destructive Actions〉
兩段的變體 — **對減法決策而言是最糟的取樣**, 因為它讓供應商涵蓋看起來最大.

分裂軸是 **session 類型**, 不是 CLI 版本. cli ≥ 0.145.0:

| kind | n | dirty-worktree | no-ask-scoped | autonomy | authority |
|---|---|---|---|---|---|
| top-level | 59 | 59/59 | 59/59 | 59/59 | 51/59 |
| **subagent** | **90** | **43/90** | **43/90** | **43/90** | **57/90** |

(第一版此表寫 subagent 0/47 — 那只涵蓋 `sessions/` 一個 store, 漏掉 `archived_sessions/`
的 129 份, 佔母體 59%. 母體數字下**沒有任何一條款對 subagent 達到全覆蓋**, 所以四條全留
的決定不變, 理由反而更強.)

而契約**確實送進 subagent**: rollout 裡它是 `role: user`, 開頭 `# AGENTS.md instructions`
的 `<INSTRUCTIONS>` 區塊, 並鏡射在 `world_state.agents_md`. 所以 subagent prompt 沒有的
條款, 沒有第二個來源. 刪掉它們等於讓**目前每一個 subagent session** — 會寫檔的那一半 —
失去「使用者未提交的工作屬於使用者, 要保留」這句話的唯一出處.

**得到的規則**: 減法必須對照**任何會載入該契約的 session 中最薄的 prompt 變體**,
不是抽樣到的那一個. 已寫進 `CodexContractRestatementTests` 的 docstring 與實際斷言.

**上表可重跑**, 不必重建分析:

```bash
scripts/codex-prompt-census.py --min-cli 0.145
```

它同時做循環性檢查 (我們自己的契約字串若出現在 host prompt 裡就警告). 刻意沒有
`--check` 模式 — 輸入是 machine-local 且本來就會變, 釘住快照只會讓非作者的人一律失敗.
它是給人看的證據, 不是 gate. `test_the_vendor_census_covers_every_justified_clause`
確保「以供應商涵蓋為由保留或刪除的每一條款」都是這支腳本的一個欄位.

**唯一真正的重述**: 外部寫入/破壞性動作的授權句 — 〈Destructive Actions〉在 subagent
側確實有 (73/77). 但仍保留, 因為兩個失效方向不對稱: 供應商若移除該段, 過度謹慎可回復,
未經授權做破壞性動作不可回復. 為 ~35 words 承擔那種形狀的尾部風險不划算.

**未動**: 語言規定, orchestration 整段, `narrowest verification that could refute`,
`DECISION:`/`[UNCERTAIN:]`, RTK — Codex host prompt 沒有 subagent/派工概念, 也沒有語言
規定, 這些是加值而非重述.

### L4 · Claude 側: 無法執行

**Claude Code 不記錄自己的 system prompt** (transcript 的 record types 裡沒有任何一種
承載它). 唯一來源是執行中 session 的 context, 而那份**混合了供應商固定文字與本機注入**,
無法可靠分離, 且 n=1.

所以 L4 在兩個 provider 上的可稽核性不對等: **Codex 可重複執行, Claude 不行.**
要補上, 需要一個等價於 rollout `base_instructions` 的擷取管道. 在那之前, Claude 契約的
既有 5 條禁述清單 (`test_claude_md_does_not_restate_the_harness_system_prompt`) 維持不變,
但要知道它的證據基礎比 Codex 側弱.

## 目前的建議

**沒有任何一條槓桿有「刪掉會讓模型犯錯」的反證, 所以沒有一條該現在動.** L4 已執行完畢,
結果是淨變動零 — 它買到的不是字數, 是那條「對照最薄變體」的方法規則, 以及一次證實:
在這種尺度下 (見開頭的 0.049%), 減法出錯的代價遠大於減法成功的收益.

L2 的 130-word 落差仍未解. 曾以為其中 47 是 Codex 重述自己的 host prompt, 實測推翻.
要查就要用原則 1 的問題去查, 不是用字數去查.

**預算口徑已於 2026-08-04 改過** (落地紀錄見
[研究摘要第 5 條](README.md#已落地-2026-08-04)).
本文的核心結論是常駐字數只佔真實 prompt 的 0.049% (p50) - 預算的價值是**規則密度的棘輪**,
不是省 token, 所以絕對字數只是密度的代理指標. 現在量密度的是三項指標 (每條規則 bytes, 規則
數, 贅詞比例), 但它們是**加在**字數上限之外: 要讓密度先綁定, codex 那份的字數上限得往上拉
約四分之一, 而沒有證據支持把常駐層放大到那個程度.
所以 L6 與測試之間的摩擦沒有消失 - 合法成長仍要改一個常數並說明理由. 改掉的是什麼算合法成長:
三項密度都還在上限內的擴充, 買到的是更好的句子而不是更多字.

## 延後項: runtime-selection eval

**定位 (本文第一版寫錯, 此處為更正)**: 它**不是**缺失的能力, 而是既有人工路徑的
**便宜替代品**. 下修預算的證據路徑一直存在 — `contract-slimming.md` 的驗收段有兩條:
真實任務回歸, 以及「無失敗 trap 的規則是刪除候選」. 它們昂貴且未自動化, 但存在.

runtime eval 想買的是把 L1 的「通過」從弱證據變成強證據, 而不必每次都跑 3–5 個真實任務.

**形狀**: 丟單一開場訊息進 fresh session, 觀測它自己載了什麼, 答案表沿用 s10 的
`ANSWERS`:

```
claude -p "<utterance>" --settings <scratch>/settings.json
       --output-format stream-json --max-turns N
  在只裝了受測描述的 scratch HOME 底下
→ 從事件流撈 Skill tool_use 的 skill 名稱
```

**可行性已確認** (2026-07-31 實測): 每次 skill 載入都是一個 `Skill` tool_use, 帶
`input.skill` = skill 名稱, 寫進 transcript; `PreToolUse` 也支援 `Skill` matcher.

### 為何延後

1. **沉默會被讀成通過.** 十八題有七題答案是 `none`, 即斷言「沒有發生」. session 當掉,
   反問, 逾時全都沒有 `Skill` 事件, 全部記成正確 — **崩得越徹底, 成績單越漂亮**.
2. **沒有 fixture hash 的等價物.** s10 的 fixture 用 SHA-256 綁在 live frontmatter 上.
   runtime eval 的輸入是**整個執行環境** (CLI 版本, settings, hook 集合, 系統提示組裝,
   模型版本), 沒有一項綁得住. 三個月後的數字不可比, **而且不會出聲**.
3. 報酬本身很小: 見開頭的尺度表.
4. 噪音: arm D 訊號是 1/3, live session 變異更大, 3 樣本分不開.

第 1, 2 點是同一類: **會說謊的 gate 比沒有 gate 糟**, 而兩者都朝「安靜地通過」壞.
這是延後的主因, 成本不是.

### 真要做時

**先解存活判準, 再寫其他任何東西** (設計筆記在 s10 的 `GROUND-TRUTH.md`). 一個 session
必須證明自己做了實質工作, 它的「沒載入」才有資格算數. grader 最後再寫, 它最簡單.

規模: 批次 trap 當**篩選**, runtime 當**確認**, 只跑打算出貨的那一個修剪, control +
該臂, 只跑關鍵題 = 8 題 × 3 樣本 × 2 臂 = 48 session.

## 重新檢視的觸發條件

以**效果訊號**為主, 字數門檻只作為次要提示:

- 某條常駐鐵律開始在真實任務中被遺漏 (驗收流程會看到)
- routing 開始誤觸或漏觸 (s10 或真實任務中出現)
- L4 稽核發現契約與供應商 system prompt 有牴觸 — 那是 bug, 優先於任何字數考量
- 需要新增常駐 skill 而無處可讓: 此時先問 L6, 再問 L1–L4
- 出現不需要 live session 就能量鑑別度的方法 (例如供應商公開 skill 選取的機率輸出)
