# 常駐 context 成本：現況與優化選項

[← 回研究摘要入口](README.md)

這份記錄**選項與其證據狀態**，不是規範。規範（判定表、預算紀律、回寫流程）在
[contract-slimming.md](../contract-slimming.md)；本文只回答「還能往哪裡省、每條路
擋在哪、什麼時候該重新評估」。

## 現況（2026-07-31 實測）

來源 `scripts/prompt-surface-census.py`；上限來源 `test_contracts.py` 的
`RESIDENT_CONTRACT_BUDGETS`、`metadata_budgets`、`per_skill_budget`。

| | 契約 | skill metadata | 常駐合計 | 餘裕 |
|---|---|---|---|---|
| Claude | 397 / 520 | 595 / 620 | 992 / 1140 | **148** |
| Codex | 527 / 540 | 515 / 540 | 1042 / 1080 | **38** |

skill metadata 逐項（兩側共用的描述逐字相同）：

| skill | words | 備註 |
|---|---|---|
| `speak-human-tw` | 176 | 單項上限 180，**只剩 4 words**。雙語各述一次，因為它是唯一會被使用者以任一語言直接叫用的 skill |
| `task-observer` | 102 | |
| `headroom-protocol` | 92 | |
| `baton-dispatch` | 88 | Claude 專有 |
| `provider-routing` | 69 | Claude 專有 |
| `experience-ledger` | 68 | |
| `leaf-dispatch` | 77 | Codex 專有，合併了上面兩支的territory |

非常駐層供對照：Claude dispatch 5080 / roles 1585；Codex dispatch 4517 / roles 1599。
這兩層是按需載入，不在本文範圍。

## 為什麼需要這份文件

**預算是單向棘輪。** 規範允許「有證據就調高」，但**沒有任何證據路徑可以調低**。
每加一支 skill 就是永久 +70～100 words。這在 Claude 側還撐得住（餘裕 148），
在 Codex 側已經是 **38 words**——大約半支 skill 的描述。下一次 Codex 側要加東西，
就會直接撞上一個沒有工具可解的決策。

所以問題不是「現在該不該瘦身」，是「等到非瘦不可的那天，手上有沒有可用的證據」。

## 槓桿

| # | 槓桿 | 上限報酬 | 證據狀態 | 擋在哪 |
|---|---|---|---|---|
| L1 | description 修剪 | ~56 words（`speak-human-tw` 176→120） | s10 arm B/C 通過 | **通過是弱證據**，不構成許可 |
| L2 | 兩份契約的落差稽核 | 未知，上限 ~130 | 未查 | 需要一次人工逐條對照 |
| L3 | 分層移出（→ skill／hook／role） | 未知 | 規範既有的第一手段，已大量套用 | 遞減報酬 |
| L4 | 刪除供應商 system prompt 已保證的行為 | 未知 | CLI 大版本後未重跑 | 需要人工對照，無機制 |
| L5 | 抑制新增（新 skill 的邊際成本） | 預防性 | 已有機制 | 不是節流，是止血 |

### L1 · description 修剪

`speak-human-tw` 是唯一顯著偏離中位數的描述（176 vs ~90），也是唯一逼近單項上限的。
s10-skill-recall 四臂實測（2026-07-31）的結論：

- 砍文件類型列舉（arm B）單獨做 — 鑑別度無損
- 砍不觸發排除項（arm C）單獨做 — 鑑別度無損
- **兩個都砍（arm D）— 精確度立刻崩**，3 樣本中 1 次把 nginx 設定檔／error log／
  Python 程式碼全導向 `speak-human-tw`

也就是說那 176 words 有一部分是**冗餘覆蓋**：兩條子句互相補位，拿掉任一條由另一條吸收。

但 s10 量的是**鑑別度**（批次分類），不是實際載入行為，證據因此不對稱：失敗是強證據，
通過是弱證據。所以 arm B／C 的乾淨結果**不構成修剪許可**——只證明「不是明顯壞的修剪」。
要把它變成許可，需要下面的延後項。

### L2 · 兩份契約的落差稽核

契約本體 Claude 397 vs Codex 527，差 130 words。規範原則 5 要求「兩契約語意同步、
字面各自最短」，但目前沒有任何測試把兩者當全文 twin 綁定——只有子句層級的存在性斷言。
所以這 130 words 的落差**沒有被檢驗過是否正當**。

**但它不是純浪費。** Codex 側把 dispatch／routing 合併成單一 `leaf-dispatch`（77），
Claude 側是 `baton-dispatch`(88) + `provider-routing`(69) = 157。Codex 少花 80 words 在
skill 層，很可能有一部分挪進了契約。兩側常駐總計 992 vs 1042 只差 50，這個讀法比
「Codex 契約肥了 130」更接近事實。

**可查證的部分**：那 130 words 裡有多少是放置差異、多少是沒壓乾淨。這是**目前報酬最高
且成本最低的一項**——不需要任何新設施，一次人工逐條對照就有答案，而且直接作用在餘裕
最緊的那一側。

### L4 · 供應商重述稽核

規範已寫明「重述 system prompt 已保證的行為是純注意力稅，一律刪」，並要求 CLI 大版本
更新後重跑。這件事沒有機制，只有紀律；本文記下它是一條**未動用**的槓桿。

## 延後項：runtime-selection eval

**目的**：把 L1 的「通過」從弱證據變成強證據——也就是取得真正的修剪許可。

**形狀**：不再問「你覺得該載哪個」，而是丟單一開場訊息進 fresh session，觀測它自己
載了什麼。

```
for utterance in <關鍵題>:
  for sample in 1..3:
    claude -p "<utterance>" --settings <scratch>/settings.json
           --output-format stream-json --max-turns N
      在只裝了受測描述的 scratch HOME 底下
    → 從事件流撈 Skill tool_use 的 skill 名稱
```

答案表沿用 s10 的 `ANSWERS` 一字不改；變的只是證據來源。

**觀測面確認存在**（2026-07-31 實測）：每次 skill 載入都是一個 `Skill` tool_use，
帶 `input.skill` = skill 名稱，寫進 transcript；`PreToolUse` 也支援 `Skill` matcher。
可行性不是問題。

### 為何延後

1. **報酬上限 5.6%**（56 words / 992），而 992 未達須動刀的程度。
2. **沉默會被讀成通過。** 十八題有七題答案是 `none`，即斷言「沒有發生」。session 當掉、
   反問、逾時全都沒有 `Skill` 事件，全部記成正確——**崩得越徹底，成績單越漂亮**。
   需要「存活判準」才能讓「沒載入」算數。
3. **沒有 `build.py --check` 的等價物。** s10 的 fixture 用 SHA-256 綁在 live frontmatter
   上，描述一漂就紅。runtime eval 的輸入是**整個執行環境**——CLI 版本、settings、hook
   集合、系統提示組裝、模型版本，沒有一項 hash 得起來。三個月後的數字跟今天不可比，
   **而且沒有東西會說它已經不可比了**。這是結構性的，不是工程做細能解的。
4. **噪音**：arm D 的訊號是 1/3，live session 變異更大，3 樣本大概分不開。
5. **歸因變糊**：量的是整份 prompt 的組裝結果，系統提示任何改動都會動結果。

第 2 與第 3 點是同一類：**會說謊的 gate 比沒有 gate 糟**，而這兩者都朝著「安靜地通過」
的方向壞。這是延後的主因，不是成本。

### 真要做時，第一件事

**先解存活判準，再寫其他任何東西。** 一個 session 必須證明自己做了實質工作
（有輸出、有工具呼叫、不以提問結尾、turn 數 > 1），它的「沒載入」才有資格算數。
grader 是整包裡最簡單的部分，最後再寫。

規模建議：不要建第二個四臂矩陣。批次 trap 當**篩選**（便宜、擋掉明顯壞的），
runtime 當**確認**，只跑真的打算出貨的那一個修剪、只跑 control + 該臂、只跑關鍵題
（U02/U05 召回，U09/U10/U11 精確度，加兩題鄰居對照）= 8 題 × 3 樣本 × 2 臂 = 48 session。

## 重新檢視的觸發條件

任一成立就該重跑這份評估：

- Codex 側常駐餘裕歸零（目前 38），或任一側需要新增常駐 skill 而無處可讓
- `speak-human-tw` 需要新觸發詞（單項只剩 4 words）
- 常駐合計逼近 1500，或 skill 數量翻倍
- L2 稽核做完且結果顯示落差不是放置差異——那表示還有便宜的空間沒撿
- 出現不需要 live session 就能量鑑別度的方法（例如供應商公開 skill 選取的機率輸出）
