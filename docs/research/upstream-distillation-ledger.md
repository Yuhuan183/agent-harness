# 蒸餾帳本: 上游每一節的去向

上游是 [mattpocock/skills](https://github.com/mattpocock/skills), pin
`068b6e0c62393147daf03530149cdce209c93da8`.

**這份帳本可以覆核.** `scripts/upstream-recheck.sh` 重新抓那個 SHA 的四個檔案並比對雜湊:

| 上游檔案 | sha256 前 16 | bytes |
|---|---|---:|
| `skills/engineering/diagnosing-bugs/SKILL.md` | `573142d28dc5a4d9` | 8614 |
| `skills/engineering/tdd/SKILL.md` | `6875cbca6b7d17be` | 3578 |
| `skills/engineering/tdd/tests.md` | `859f9e592c188fda` | 2214 |
| `skills/engineering/tdd/mocking.md` | `3ceb807fdf4a47d6` | 1481 |

腳本綠的意思是「這份帳本描述的就是這些位元組」. 它紅的意思是抓取有問題或雜湊打錯 ——
上游**移動**不會讓它紅 (SHA 釘的是內容), 那要重新解析 marketplace pin 拿到新的 SHA,
再用新 SHA 跑一次才看得出哪些檔案真的變了.

`references/` 這個路徑是錯的: 兩份 reference 在 `tdd/tests.md` 與 `tdd/mocking.md`,
不在子目錄底下. 2026-08-17 的第一版 ATTRIBUTION 寫錯, 已更正.

## 上游一動, 這些要一起動

pin 散在 **7 個檔案**. 更新其中六個而漏掉第七個, 那一個會繼續描述另一份文本 —— 而且是靜默的,
正是釘 SHA 要防的那件事. `test_every_document_naming_the_upstream_pin_names_the_same_one`
守住這一點: 每個站點都要帶當下的 pin, 而兩份 ATTRIBUTION 要帶完整 40 位 (它們扛的是授權義務).

沒有單一來源可用: 兩份 ATTRIBUTION 部署到 repo 之外要能獨立成立, 而腳本需要一個跑得起來的預設值.
所以是**檢查一致**而不是共用一份.

### 順序

| # | 檔案 | 改什麼 | 為什麼是這個順序 |
|---|---|---|---|
| 1 | `scripts/upstream-recheck.sh` | 預設 SHA 與四個雜湊 | 先讓覆核工具指向新版, 否則後面每一步都在對舊的比 |
| 2 | `docs/research/upstream-distillation-ledger.md` (本檔) | 雜湊表 + 逐節處置 | **逐節重分類**, 不是只改 SHA. 差異可能落在任何一節 |
| 3 | 兩份 `ATTRIBUTION.md` | Reviewed commit, release, 分類 | 分類要照 2 的結果改, 不是憑印象 |
| 4 | `main/.agents/skills/*/SKILL.md` 與 `references/tuning.md` | 只有決定採納時才動 | 動了就要重量預算並重新部署 |
| 5 | `docs/research/mattpocock-skills-integration.md` | 版本對照表 + 精讀紀錄 | 舊 pin 保留為歷史, 不要覆蓋 |
| 6 | `docs/research/README.md` | 時效性基準那一列 | |
| 7 | `docs/plans/engineering-workflow-distillation.md` | 相依處置表 | 只有當上游改動影響那四項相依時 |

### 每次都要做的三件

- **先抓再分類.** 第一次蒸餾是讀過就寫, 四處少算上游. 現在的順序是抓 → 逐節列表 → 分類;
- **重分類每一節**, 不只看已經列出來的條目. 少算的那四處對只檢查現有條目的人是隱形的;
- **pin 前進不等於要跟進.** 逐節判 adopt / adapt / already-covered / reject, 判完才動 SHA.

## 目的: 蒸餾要達成什麼

上游是一整套二十五個 skill 的工作流, 假設有 issue tracker, 有 `CONTEXT.md` 與 ADR,
有 TypeScript 與 Jest. 本專案要的不是那套工作流, 是其中**在任何 repo 都成立的判準**,
而且要能被本專案既有的授權與驗證規則接住.

所以蒸餾的判準是三條:

1. **可攜** —— 拿掉上游的工具假設之後還站得住的才留;
2. **能被本專案的規則接住** —— 上游沒有授權分離, 本專案有, 蒸餾版要補上;
3. **本專案付得起** —— 每個 skill 的 name 與 description 是每個 session 都付的常駐成本.

## `diagnosing-bugs` → `evidence-debugging`

上游 13 節, 逐節處置:

| 上游節 | 處置 | 去向 |
|---|---|---|
| frontmatter 觸發語 (diagnose/debug, broken/throwing/failing/slow) | **近似沿用** | `SKILL.md` frontmatter, 另加繁中觸發語 |
| `CONTEXT.md` + ADR 開場 | **刪除** | 改指 `AGENTS.md` 與 `docs/architecture.md` |
| Redact | **近乎逐字** | `SKILL.md` → Redact before you show anything |
| Phase 1 「這就是這個 skill」 | 概念重寫 | `SKILL.md` → The gate 的開場 |
| Ways to construct one (十種) | **濃縮成八種** | `SKILL.md` → The gate 末段 |
| Tighten the loop | **刪除** | 見下方「捨棄了什麼」 |
| Non-deterministic bugs | 概念重寫 | `references/tuning.md` → 量到的重現率, 前後都要引用 |
| When you genuinely cannot build a loop | 概念重寫 | `SKILL.md` → The gate 末段 |
| **Completion criterion** | **近乎逐字** | `SKILL.md` → The gate 的四條判準 |
| Phase 2 Reproduce + Minimise | 概念重寫 | `SKILL.md` → Then 1–2 |
| Phase 3 Hypothesise | 概念重寫 | `SKILL.md` → Then 3 |
| Phase 4 Instrument | 概念重寫 | `SKILL.md` → Then 4 |
| Phase 5 Fix + regression test | 概念重寫, 其中「沒有正確的 seam, 那件事本身就是發現」**近乎逐字** | `SKILL.md` → Repair |
| Phase 6 Cleanup | 濃縮成一句 | `SKILL.md` → Repair 末句 |

**本專案新增, 上游沒有的**:

- 授權分離 —— 上游 Phase 5 直接從診斷走進修復, 中間沒有閘. 蒸餾版把診斷與修復分成兩種授權,
  模糊算診斷;
- seam 必須抵達可觀察結果 —— 來自 2026-08-17 的本機事件, 上游的 tautological 分類涵蓋不到
  這個形狀 (斷言是真的, 但與結果無關);
- 「症狀從未被按需產生時, 改動後沒再出現不構成證據」—— 上游以 red-capable 隱含, 明寫成獨立
  規則是本地的.

## `tdd` → `test-first-change`

上游本體只有 38 行, 實質在兩份 reference. 逐節處置:

| 上游節 | 處置 | 去向 |
|---|---|---|
| frontmatter 觸發語 (red-green-refactor, integration tests) | 重寫 | 觸發語改成本專案的動詞, 另加繁中 |
| `CONTEXT.md` + ADR 開場 | **刪除** | 同上, 改指既有 owner |
| What a good test is | 概念重寫 | `SKILL.md` → Then 1 (斷言可觀察結果) |
| **Seams — 定義那一句** | **近似改寫** | `SKILL.md` → Seam, defined here |
| Seams — 「只在事先議定的 seam 測, 未確認的不寫」 | **刪除** | 與本專案「不問 repo 已回答的事」相斥; 換成從程式碼推導, 只在兩個候選會產生實質不同的檢查時才問 |
| Seams — `codebase-design` 指標 | **刪除** | 不導入該 skill, 留指標等於留斷掉的指令 |
| 反模式 Implementation-coupled | 概念重寫, 分散 | `SKILL.md` → Mocking 與 Seam 的 Reach/Observability |
| **反模式 Tautological** | **採用該分類**, 並拆成兩類 | `SKILL.md` → 不會失敗的斷言 1 與 2 |
| **「期望值必須來自獨立的真相來源 —— 已知字面值, 算過的例子, 規格」** | **近乎逐字** | `SKILL.md` → Then 1 |
| 反模式 Horizontal slicing | 採用否定面 | `SKILL.md` → Never 「不要一次寫完所有檢查」 |
| **Vertical slices / tracer bullet (正面規則)** | 2026-08-17 補回 | `SKILL.md` → Then 3 |
| Rules: Red before green | 概念重寫 | `SKILL.md` → The gate |
| Rules: One slice at a time | 概念重寫 | `SKILL.md` → Then |
| **Rules: 「Refactoring 不屬於這個迴圈」** | **近乎逐字** | `references/tuning.md` → Authority |
| `tests.md` 好壞測試範例 (TypeScript + Jest) | **範例重寫** | `references/tuning.md` → Worked pairs, 改成本 repo 的 Python / shell / markdown |
| `mocking.md` 上半 (只在系統邊界 mock) | 近似 | `SKILL.md` → Mocking |
| `mocking.md` 下半 (dependency injection, SDK 式介面) | **刪除** | 見下方 |

**本專案新增, 上游沒有的**:

- seam 的 Reach / Observability 兩分 —— 上游只說 seam 是公開邊界, 沒有「碰得到動作碰不到結果」
  這個區分;
- 「不會失敗的斷言」第 3 與第 4 類 (碰不到結果 / 從未見紅);
- 進場閘的第二條 —— 因為函式還不存在而失敗, 是編譯錯誤不是觀察到的失敗;
- 一句話抓全部四類: 我要改什麼才會讓這條變紅;
- 授權分離, 以及對 `evidence-debugging` 的指路.

## 上游有而我們捨棄的

分成兩類. **有意識刪除**的已列在上表, 理由都在 ATTRIBUTION; 這裡是完整清單與代價.

| 捨棄的 | 為什麼 | 代價 |
|---|---|---|
| `CONTEXT.md` + ADR 依賴 (兩個 skill 開頭) | 計畫非目標明文不新增這些根文件 | 無 —— 既有的 `AGENTS.md` 與 `docs/architecture.md` 接得住 |
| `scripts/hitl-loop.template.sh` (feedback loop 第 10 級) | 本 repo 的驗證面沒有「必須有人點擊」的情境 | 無 —— 留一個未實作的指標比沒有更糟 |
| `codebase-design` 全套語彙 (module / depth / adapter / leverage / locality) | 不導入該 skill | 有 —— 蒸餾版只帶 seam 一個詞, 談模組深度時沒有共用語彙 |
| 「未確認的 seam 不寫測試」硬阻斷 | 與本專案「不問 repo 已回答的事」相斥 | 有 —— 少了一道確認, 換成從程式碼推導的判斷 |
| **`diagnosing-bugs` 的 Tighten the loop** | 2026-08-17 第一次蒸餾時漏掉, 不是決定 | **有** —— 「把迴圈當產品去收緊」是上游一條實質建議 (更快 / 訊號更利 / 更確定), 蒸餾版只要求 fast 與 deterministic, 沒有要求**改善**它 |
| **`mocking.md` 下半 (DI 與 SDK 式介面)** | 同上, 漏掉 | 有 —— 那是「怎麼設計成好 mock」的建議, 屬於設計而非測試判準, 落在本 skill 邊界外, 但當初沒有記錄這個判斷 |
| 上游其餘 23 個 skill | 第一批只取兩個 | 見[導入研究](mattpocock-skills-integration.md)的分組表 |

## 這份帳本是怎麼來的

2026-08-17 第一次蒸餾時**讀過就寫**, 沒有留逐段對照. 分類憑印象, 而印象在「這段是我自己想的」
那個方向上系統性地偏樂觀 —— 事後重新抓上游比對, 找到四處少算與兩處未記錄的刪除.

少算是計畫明說唯一不能弄錯的方向 (把 substantial portion 說成概念重寫). 所以現在的做法是:
**先抓上游, 逐節列表, 再寫分類**, 而不是讀完憑印象分類. `scripts/upstream-recheck.sh`
讓下一次覆核從同一個起點開始.
