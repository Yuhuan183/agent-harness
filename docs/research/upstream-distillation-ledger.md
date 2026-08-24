# 蒸餾帳本: 上游每一節的去向

上游是 [mattpocock/skills](https://github.com/mattpocock/skills), pin
`885e2ca4d842d139e9aef4e48d366c63cb1b8013`.

**這份帳本可以覆核.** `scripts/upstream-recheck.sh` 重新抓那個 SHA 的四個檔案並比對雜湊:

| 上游檔案 | sha256 前 16 | bytes |
|---|---|---:|
| `skills/engineering/diagnosing-bugs/SKILL.md` | `77f3cf31bc99b2f4` | 8529 |
| `skills/engineering/tdd/SKILL.md` | `cb01f66bebfaa25f` | 3549 |
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

## 2026-08-24 重查: 上游前進五個 commit, 我們的兩個來源檔一個位元組沒動

`885e2ca4d842d139e9aef4e48d366c63cb1b8013` -> `5b15a47f2d7150f545fbcacbfe381787fc0230dc`, 五個 commit,
2026-08-20 到 08-21.

**查了什麼.** 用 blob SHA 直接比對兩個來源檔在 pin 與 head 的內容:
`skills/engineering/diagnosing-bugs/SKILL.md` 兩端都是 `061c25a5`,
`skills/engineering/tdd/SKILL.md` 兩端都是 `8fc08671`. 逐位元組相同, 所以
`evidence-debugging` 與 `test-first-change` 的分類不必重跑, pin 推進純屬記帳.

五個 commit 動到的是別的地方: `skills/productivity/grilling/SKILL.md` (+7/-1,
純排版 —— 在連續問題之間加一條 `---`), 兩個 changeset, 一行 `.gitignore`,
以及一個**新 skill**.

### 新 skill `implement-spec`: 逐條分類

上游把它放在 `skills/in-progress/`, 並標 `disable-model-invocation: true` ——
它自己說這是未完成的東西. 但它談的是派工拓樸, 和 `baton-dispatch` 同一層, 所以
逐條看:

| 上游規則 | 處置 | 依據 |
|---|---|---|
| ticket 是 **task graph** 不是步驟清單, 永遠有一個 **frontier** | 佐證 | 我方的 program envelope 與 slice 已有 prerequisites 與 ready envelope; 「frontier」這個詞沒有, 而它指的是**同時可抓的全部**, 我方是一次一個 slice |
| 溝通稀疏, 主要用 **context pointer**, 不重複 pointer 已經帶到的資訊 | 佐證 | `SKILL.md` 的「Brief only minimum paths」與 brief 模板的「Minimum sources」是同一個工具; 上游多的那半句 (指了就別再貼一次) 見下方 |
| implementer 盡量背景執行以求最大並行 | 已落地 | 「Launch every selected agent in one independent batch back-to-back」 |
| exploration agent 把筆記存到 **repo 外的共用目錄**給後續 agent 讀 | 不採用 | 形狀不同: 我方所有綜合走 main, leaf 之間不交換產物. 共用暫存目錄會生出第二個整合點而且沒有 owner, 與不變量 1 (一個可寫 artifact 一個 owner) 相斥 |
| 每個 implementer 有自己的 worktree 與 branch | 已落地 | 「isolated workspaces for competing writes」 |
| 由 **merger subagent** 把完成的工作併回 PR 分支 | 不採用 | 形狀不同: 契約明文 main 擁有 integration 與 synthesis. 把合併派出去等於把最終判斷派出去 |
| 每次完成後重算 frontier, 再開更多 implementer | 佐證 | 同第一列 |
| 全部完成後跑 code review, 所有問題**用單一 subagent** 修 | 已落地 | 「run expensive or repository-wide gates after integration」加上 verifier 放在最小完整驗收邊界 |
| 收尾清掉所有 worktree | 已落地 | QC 會抓 leaf 留下的暫存檔; worktree 由 runtime 的 `isolation: "worktree"` 自動清 |
| `disable-model-invocation: true` | 佐證 | 我方不用這個欄位, 改由契約規定「決定要派工之後才載入」—— 機制不同, 意圖相同 |

### 那半句沒有落地, 理由寫在這裡

上游說「不要重複 pointer 已經帶到的資訊」. 我方有「Brief only minimum paths」
(給幾個指標) 但沒有明說「已經給了路徑就別把內容再貼一次」. 這在我方的形狀下**更**
成立, 因為 leaf 拿不到對話歷史, 所以 main 得決定什麼內嵌什麼指過去.

沒有落地的理由是成本: `baton-dispatch/SKILL.md` 現在 1298/1300 字, 只剩兩個字的
餘裕, 加一條子句要嘛擠掉別的, 要嘛帶著量測與理由調高天花板. 而這條規則目前**沒有
對應的本機失效** —— 沒有任何一次 QC 抓到「brief 把指過去的內容又貼了一遍」.
為一個意圖付預算, 正是這個 repo 說過不做的事.

**推翻條件**: 出現一次 QC 或 replay 觀察到 brief 同時給了路徑又貼了該路徑的內容,
就落地, 並在同一次 commit 帶上量測與理由.

### pin 為什麼沒有跟著動

第一版把 pin 推到了預設分支的 head, 那是錯的, 而且是安靜地錯: `Reviewed commit` 記的是
**marketplace 送出什麼**, 2026-08-17 解析出 `885e2ca4`, 而 `upstream-pin-report.py` 比的是
**預設分支**. 兩者是不同的東西 —— 這份研究本身就是為了那個差別而寫的 (marketplace pin
超前 tag, 而 version 不動). 把後者寫進前者的欄位, 等於把整份研究的結論從紀錄裡拿掉,
而且沒有任何檢查會紅.

所以 pin 留在 marketplace 那一個, 另外加一列記預設分支查到哪裡. 這台機器沒有安裝 Claude
plugin, 解析不了當前的 marketplace pin, 所以那一列只能是「預設分支到 X, 我們的檔案沒動」.

**代價要講明白**: `upstream-pin-report.py` 會一直把這個上游報成 MOVED, 因為它比的是預設
分支. 那不是誤報, 是它問的問題和 pin 記的東西不同. 要讓它停下來, 要嘛在這台機器上裝
plugin 去解析 marketplace pin, 要嘛讓報告讀 `Upstream skill` 那一列去回答「我們的來源檔
動了沒有」而不只是「分支動了沒有」. 後者比較便宜, 也比較接近真正的問題.

### 順帶修掉一個編出來的數字

同一次還把研究摘要的「25 skills」改成「26」, 理由是「上游多了一個 skill」—— 那是推的,
不是數的. 實際數 (`skills/*/*/SKILL.md`) 在 pin 是 35, 在預設分支 head 是 36, 其中 7 個在
`in-progress`. 原本的 25 也從來沒有人驗過. 現在那一格帶著計數規則與所在 commit.

### 沒有查的

`grilling` 之外的其他上游 skill 沒有重看 (head 上共 36 個, 我們取兩個) —— 這次只回答
「我們的來源動了沒有」與「新出現的東西要不要」. 上游那五個 commit 以外的歷史沒有重新
溯源. 當前的 marketplace pin 也沒有重新解析, 理由如上.
