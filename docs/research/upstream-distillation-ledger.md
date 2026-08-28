# 蒸餾帳本: 上游每一節的去向

這份帳本記**逐節處置**. 到 2026-08-28 為止它只寫過一個上游, 而那是歷史造成的不是分工造成的
—— 其他上游的處置散在各自的文件裡 (speak-human-tw 有自己一份, cablate/baton 在
[peer-harnesses](peer-harnesses.md), fable-method 在 [trap-experiments](trap-experiments.md)),
只有 `rebelytics` 一個**哪裡都沒有**. 2026-08-28 的對應性檢查抓到那個洞, 補在本檔末節.

| 上游 | pin | 逐節處置在哪 |
|---|---|---|
| [mattpocock/skills](https://github.com/mattpocock/skills) | `885e2ca4d842d139e9aef4e48d366c63cb1b8013` | 本檔主體 (下方全部各節) |
| [rebelytics/one-skill-to-rule-them-all](https://github.com/rebelytics/one-skill-to-rule-them-all) | `281f13466cd3a73e9ebc9d210907748e1941a3dd` | 本檔[最後一節](#rebelyticsone-skill-to-rule-them-all-逐條處置-2026-08-28) |

**下面每一節, 除了最後一節, 講的都是 mattpocock/skills.**

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
- **重分類每一節**, 不只看已經列出來的條目. 只檢查現有條目的人看不到少算的那四處;
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

沒有落地的理由有兩條, 而**第一條在 2026-08-28 查出來是錯的**.

~~成本: `baton-dispatch/SKILL.md` 現在 1298/1300 字, 只剩兩個字的餘裕.~~
**1298/1300 是 `provider-routing/SKILL.md` 的數字**, 被寫到了 baton 頭上.
當場量 (`budget-drift-report.py` 的同一支 `word_count`): `baton-dispatch` 是
**1269/1297, 餘裕 28 字 (2.2%)**, 而且它根本不在報告的「under 2% headroom」那張表裡 ——
那張表上有九份檔案, 沒有一份是它. 一句話塞得下, 不必位移也不必調高天花板.

**第二條理由仍然成立, 而且它本來就是承重的那一條**: 這條規則目前**沒有對應的本機
失效** —— 沒有任何一次 QC 抓到「brief 把指過去的內容又貼了一遍」. 為一個意圖付預算,
正是這個 repo 說過不做的事. 處置因此不變, 但**理由只剩一條**, 而且是比較弱的那一種
(缺證據, 不是缺空間).

這則本身值得記: 兩條理由並列時, 只要有一條是硬的 (數字), 另一條就不會被檢查. 而錯的
正好是硬的那一條 —— 它看起來最不需要複查.

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

## 2026-08-28 重查: 上游再前進三個 commit, 兩個來源檔仍然一個位元組沒動

`5b15a47f2d7150f545fbcacbfe381787fc0230dc` -> `6654f6b60cd9d5be8b54c6fafe44346dabeb3b76`,
三個 commit, 全在 2026-08-24. 累計對 marketplace pin `885e2ca4` 已經是八個 commit.

**查了什麼.** `scripts/upstream-recheck.sh` 對舊 pin 與新 head 各跑一次, 四個檔案
兩次全部 matches the ledger —— 不只是「compare 說沒動到」, 是重抓後逐位元組相同.
`evidence-debugging` 與 `test-first-change` 的分類不必重跑.

三個 commit 動的全是同一件事: 一個**新 skill `retro`**, 加上它的 `agents/openai.yaml`
與 `in-progress/README.md` 的一行索引. 沒有碰 `engineering/`.

### 新 skill `retro`: 逐條分類

上游自己標了三重保留 —— `in-progress/` 桶, `disable-model-invocation: true`, 索引
裡寫 `STUB: design notes only, not functional yet`. 依蒸餾規則這要**降低權重**. 但它
談的是「怎麼改善 agent 的環境」, 和本 repo 的 `task-observer` + `experience-ledger` +
架構文件同一層, 所以還是逐條看:

| 上游規則 | 處置 | 依據 |
|---|---|---|
| 先載 `writing-for-agents` 取寫作規範 | 不採用 | 形狀不同: 我方的寫作規範是 repo 規則 (`docs/README.md` 6-8) 加 `readable-zh-tw`, 由 `zh-tw-usage-report.py` 與 contract tests 盯, 不是 retro 流程裡的一次載入 |
| 讀該 session 的**第一手來源**, 必要時翻本機 session log; 未指定就用當前 session | 已落地 | `evidence-debugging` 要求跑得出來的重現而非回憶; `experience-ledger` 的 hook 直接從 transcript 取 route (`route_source: transcript-verified`); `context-inflow-report.py` 讀本機真實 session 算窗口組成 |
| 候選類別: **Navigation** —— 找檔案花多久, 有沒有隱性相依, 要不要加導航指標 | 已落地 | `docs/README.md` 規則 1 (一條規則一個真相源, 其餘連結指過去) 與「依目的閱讀」入口就是這件事 |
| 候選類別: **Automated checks** —— 哪些錯誤可以被 lint/type/test 攔下 | 已落地, 而且更細 | `docs/architecture/architecture.md` 軸二把手段分成散文/措辭/承載物/閘/儀器五級, 各帶強制力, 可觀測性與本機證據. 上游的「加個自動檢查」是這張表的第四級 |
| 候選類別: **Coding standards** —— 該給 **reviewer agent** 加規則, 而不是給實作者 | 已落地 | `harness-review` 是 repo-root dev-only, 明文不進部署清單 —— 審查規範本來就不在常駐面, 只在審查時載入. 上游的成本論證 (實作者上下文壓力最大, 審查者拿到的是 diff) 與我方軸一 (常駐/派工/拉取/機械, 誰付幾次) 是同一個論證的兩種座標 |
| 候選類別: **Global AGENTS.md** —— 太大時把 steering 指令移去標準或檢查 | 已落地 | 字數預算是棘輪, 成長要位移或帶量測調高; `prompt-surface-census.py` 分 resident/dispatch/roles 三桶, `budget-drift-report.py` 讀歷史看棘輪有沒有變橡皮圖章 |
| 候選類別: **Tool economy** —— 昂貴或 token 效率差的工具呼叫與自訂 MCP | 部分落地 | `usage-report`, `codex-usage`, `headroom-protocol` 各管一段; `context-inflow-report.py` 量的正是「窗口實際被什麼填滿」. 沒有的是把它當成**回顧時的固定提問**, 而不是想到才跑 |
| 候選類別: **No-ops** —— 找出 steering 檔裡不改變行為的指令 | **佐證, 並暴露一個缺口** | 見下節 |
| 候選類別: **Information access** —— 提高 agent 拿得到的資訊 (tee dev server log, 第三方唯讀權限) | 佐證 | 本 repo 十支「只報不擋」的腳本就是這條的實作, 軸二把「儀器」列為可觀測性最高的一級, 理由一模一樣: 閘只在攔下來時留痕, 儀器連「什麼都沒發生」都回報 |
| 候選依**嚴重度**排序呈現 | **不採用 —— 這是一處實質分歧** | 見下節 |
| `CLAUDE.md`/`AGENTS.md` 進每個 agent 的窗口, 要極省著用, 通常只放導航指標 | 已落地 | 軸一那張表逐格寫明誰付幾次, 並且點出反直覺的那條: skill 的 `description` 是常駐的, 本文不是 |
| `CODING_STANDARDS.md` 在審查時讀而非實作時讀; 超過 1,000 行加導航指標 | 形狀不同 | 同「Coding standards」那列; 我方沒有這個檔, 對應物是 dev-only skill 加 `docs/` 拉取層, 而 `docs/` 刻意沒有字數預算 |
| docs 當被指過去的參考檔; 寫新的之前先找現有的 | 已落地 | `docs/README.md` 規則 1 與 4, 由 `document-inventory.json` 與 `test_document_inventory.py` 界定 |
| skill 用來放文件 (因為 description 會進窗口) 或使用者觸發的指令 | 已落地 | 同軸一; census 就是按這個切桶的 |
| `agents/openai.yaml` 帶 `allow_implicit_invocation: false`, 與 `disable-model-invocation: true` 成對 | **佐證 —— 但這條不是這次才有的, 見下節** | 上游把同一條規則落在兩個 provider, 各用該側的慣用寫法, 那正是本 repo 的雙生規則. 我方軸一也已經記過這個欄位的成本後果 (Codex 上 `allow_implicit_invocation: false` 的 skill 連 description 都不注入) |

### 這條佐證在樹上躺了一個半月, 三次重查都沒看見

`agents/openai.yaml` **不是 `retro` 帶來的**. 它是 2026-07-13 的
`feat: add Codex agents/openai.yaml metadata to every skill` 一次鋪到每一支
skill 的慣例, 在我方 pin `885e2ca4` 上就已經有 35 份, 到 head 是 37 份 —— 每一支
skill 都有一份, 沒有例外.

也就是說: **本 repo 最看重的那條規則 (同一條規則落在兩個 provider, 各用該側的
慣用寫法), 上游一直在做, 而我們三次重查都沒有把它記下來.**

**為什麼會漏.** 三次重查問的都是同一個問題 —— 「我們取的那幾個 `SKILL.md` 動了
沒有」, 加上「diff 裡有沒有新東西」. 這兩個問題都答對了, 而且答案都是對的. 漏掉的
是第三個問題: **上游這棵樹的形狀本身有沒有在講一條規則.** 每一支 skill 旁邊都掛一份
另一個 provider 的設定檔, 這件事不會出現在任何一次 diff 裡, 因為它從來沒有變過.

蒸餾規則裡「重新分類每一條, 不是只看已經列出來的那些」講的正是這件事, 而這次是它第
一次在**新增以外**的方向上被驗證: 已經列出來的條目會被重看, 從來沒被列出來的不會.

**下次怎麼不再漏**: 重查時除了讀 diff, 至少對 head 的 tree 做一次形狀清點 ——
數一數有幾種副檔名, 有沒有哪個檔名在幾乎每個目錄裡都出現. 這次的 tree API 一次呼叫
就答得出來, 成本是一行 `recursive=1`.

### No-ops: 我們量過, 但沒有在掃

上游把「找出不改變行為的指令」列成回顧類別. 本 repo 不只同意, 還**量到過一個** ——
「在契約裡提到一支 skill 會不會讓它比較容易被載入」問了兩次, `s11` 跑 90 個 run,
replay 的 `d1`/`d2` 又在派工路徑上加 21 個, 答案都是**零位移**. 同一把尺沒有瞎:
2026-08-15 拿掉語言子句, 中文輸出從 5/5 掉到 0/5.

所以方法有, 證據有, **例行的掃描沒有**. 缺的不是儀器而是提問時機: 目前一條子句要被
懷疑成 no-op, 得有人先想到去為它設一次對照.

**為什麼不現在補一支腳本.** 架構文件在相鄰的一個問題上已經寫過理由, 而且適用:
「那是讀紀錄的判斷不是腳本查得到的事實 —— 寫一支只會產出誤報, 而誤報比留白糟」.
一支「找不改變行為的句子」的腳本, 在靜態文本上分不出「沒人違規」與「規則無效」,
那正是軸二說儀器才分得出來的那件事, 而分得出來的儀器是 eval, 不是 grep.

**落地的是提問, 不是腳本**: 上游這條的價值在把它變成**回顧時必問的一格**, 而不是
靈光一閃. 這次不動 skill 本體 —— `task-observer` 是使用者授權才寫的質性紀錄, 塞一張
七格清單進去會把它變成背景遙測, 那是它 ATTRIBUTION 明文改掉上游設計的地方.

**推翻條件**: 出現第二個被證實的零位移子句, 而它是靠有人偶然想到才被抓到的, 就把
這七格清單落到一個明確的位置 (最可能是 `harness-review` 的檢查面, 因為它已經是
dev-only 且不進部署清單), 並在同一次 commit 帶上量測與位移.

### 排序分歧: 嚴重度 vs 證據強度 × 成本

上游說「依嚴重度排序呈現候選」. 本 repo 的研究摘要**明文拒絕**這個排法:

> 排序原則是**證據強度 × 成本**, 不是影響力大小. 理由: 影響力是估出來的, 查得到的是
> 前兩者. 用估出來的量當主排序鍵, 等於讓最會講故事的那條排第一.

兩邊都不是筆誤, 而是對同一件事的不同判斷. 上游的排法在**人來裁決**的場景下比較自然
—— 嚴重度是人一眼就估得出來的東西. 我方的排法防的是**agent 自己產生候選**時的偏誤:
估出來的影響力由產生候選的那一方給, 它沒有成本去高估.

**什麼會了結這場分歧**: 本機累積到夠多的改善候選, 兩種排法各跑一次, 比對前三名的
實際落地效果. 目前候選數不足以支撐這個比較, 所以兩種立場都記著, 不挑近的那個.

### 沒有查的

上游 head 上共 37 個 `skills/*/*/SKILL.md`, 這次只讀了新增的 `retro` 與它的
`openai.yaml`; 其餘 skill 沒有重看. `grilling` 在 2026-08-20 的排版改動已在
[08-24 那節](#2026-08-24-重查-上游前進五個-commit-我們的兩個來源檔一個位元組沒動)
處置過, 這次沒有重新分類. **當前的 marketplace pin 依舊沒有重新解析** —— 這台機器
沒裝 Claude plugin, 理由與代價同上一節.

這次做了一次 tree 形狀清點 (`recursive=1`), 抓到 `agents/openai.yaml` 那條; 但清點
只做了「檔名在幾乎每個目錄裡重複出現」這一種形狀, 沒有查 `.changeset/`,
`plugin.json` 或 README 分桶規則裡有沒有別的規則. 那些仍然沒查.

## `rebelytics/one-skill-to-rule-them-all` 逐條處置 (2026-08-28)

**為什麼這麼晚才寫.** `task-observer` 從這裡蒸餾, 而它是五個上游裡**唯一沒有研究層紀錄**
的一個: ATTRIBUTION 有一段摘要 (「activation 與寫入改成明示 opt-in, 可變的編號 Markdown log
換成 append-only 上鎖的 JSONL 事件帳本, Git checkout 為真相源, 禁止自動編輯/部署/commit/
刪除/排程套用」), 但摘要不是逐條分類. 2026-08-28 的對應性檢查抓到.

**查了什麼.** 重抓 pin `281f13466cd3a73e9ebc9d210907748e1941a3dd` 的四個檔, 讀的是位元組
不是我方摘要:

| 上游檔案 | sha256 前 16 | bytes |
|---|---|---|
| `SKILL.md` | `60bfdcd99c4678a8` | 24492 |
| `references/weekly-review.md` | `247e7bfcd4aecc71` | 10520 |
| `references/skill-authoring.md` | `15fc47365fdfc89c` | 12185 |
| `references/environments.md` | `0e4274047c6628e8` | 4950 |

### 逐條

| 上游規則 | 處置 | 依據 |
|---|---|---|
| session 開始時若 log 檔不存在就**自動建立** | **不採用** | 我方 activation 與寫入一律明示 opt-in; 「列出不存在的帳本不得建立它」是明文規定 |
| 工作區若落在**短命路徑** (worktree, 暫時 clone) 要警告並改錨到穩定專案路徑 | **已落地, 而且更強** | 我方帳本固定在 `~/.agents/telemetry/`, 絕對路徑, 結構上進不了 worktree. 上游用**提醒**解, 我方用**位置**解 —— 同一個危害, 我方那一側不需要模型記得 |
| session 開始掃描 OPEN 觀察並「放在意識裡」 | **不採用** | 那是背景啟動; 我方只在摩擦發生後觸發 |
| `last-review-date.txt` 用字面值 `never`; 超過 7 天且有 OPEN 才提議; **絕不擋使用者的工作** | **形狀不採用, 原則已落地** | 我方沒有 session-start 掛鉤, 所以前兩句無處可放; 「絕不擋工作」等同我方「先處理修正, 不要用回饋問題打斷復原」 |
| 每個 session 提議一次: 把啟動指令加進 `CLAUDE.md` | **不採用** | skill 自我安裝進使用者契約, 正是我方契約禁止的 |
| 記下 log 的 mtime; 每次 append 前重讀; **絕不相信記住的編號** | **已落地, 而且搬離了模型** | 我方用排他檔案鎖寫入, 共享鎖讀取, append-only JSONL 加 UUID. 上游是要求**模型**小心地維護一份 Markdown; 我方把它交給工具 |
| 整個 session 全程 active, 連檢討與後設討論都算 | **不採用** | 我方只在明確不滿或要求修正之後觸發 |
| **每完成第 3 個 TodoWrite 就強制寫一次 log**, 沒觀察也要寫一行 `no observations` 標記 | **不採用, 但它的理由是本輪最重要的佐證** | 見下節 |
| **deliverable-event flush**: 把寫入掛在本來就會發生的工具呼叫上 | **不採用 (同上), 理由同樣是佐證** | 見下節 |
| 引用觀察編號時, 編號**只能來自紀錄自己的識別欄位**, 絕不能來自搜尋工具的位置後設資料 (`grep -n` 的行號被當成觀察編號), 另加一層「和計數器範圍比對」的合理性檢查 | **已落地 (機制), 一般化那條不落地 (無本機失效)** | 我方 ID 是腳本回傳的 UUID, 和行號長得完全不一樣, 該失效在我方形狀上發生不了. 一般規則本身好, 但本 repo 沒有一筆對應失效, 而為意圖付常駐預算是這裡說過不做的事 |
| 分類法: open-source / internal, 兩可時預設 open-source 並剝掉細節; 這條界線同時是保密界線 | **已落地** | `--type open-source\|internal`, 以及「概括原則, 專案細節用 internal」 |
| **Archival on Write**: 已解決的條目搬進日期檔; 解決狀態**必須**記日期; 寬限期放在檔案裡不放 session 記憶; 且要備份→重讀→合併→驗證條目數 | **不採用, 形狀不同 —— 而這是我方設計最強的一次佐證** | 我方 append-only, 解決是**追加一個事件**, 從不改寫也不搬移. 上游自己寫著 archival 是「這份 log 承受的最高風險變更, 而且在生產環境**已經毀掉過並行的 append**」—— 那整類危害在我方設計裡不存在 |
| 不要記: 一次性且不通用的修正, skill 已涵蓋的偏好, 與方法無關的工具 bug, 需要專有資訊才有用的觀察 | **已落地** | 逐條對應我方的 Boundaries |

### 那兩條「不採用」的理由, 是第三個獨立血緣撞上同一面牆

上游把「每完成第 3 個 todo 就強制寫」寫成硬檢查點, 而它給的理由是自己踩過:

> 這個 skill 已經證明, 比較軟的「完成項目時檢查一下」或「暫停並自問」在**認知負荷高的分析
> 工作中會消失**, 而那正是觀察累積最多的時候. **寫入本身就是強制機制**.

以及:

> **硬強制掛在你本來就會做的工具呼叫上, 是唯一可靠的機制**; 依賴記憶的軟提示撐不過長時間
> 實質工作中的認知負荷.

**這幾乎是本 repo [軸二](../architecture/architecture.md#軸二-憑什麼算數)的逐句重述** ——
散文是權重不是強制力; 承載物本身沒有強制力, 但它讓違規變成機械可判定的事實.

**這是第三個彼此獨立的作者走到同一個結論**, 而票怎麼數, 三家有沒有共同祖先, 以及這對
第二輪的發現二有什麼影響, 全部寫在[跨上游整合第二輪](cross-upstream-synthesis.md#跨上游整合第二輪-2026-08-28-進行中)
的「第三個獨立血緣」一節 —— 跨上游的收斂是那份文件的職責, 這裡只記本上游的處置.

**我方仍然不採用那兩條**, 而理由要說得比「形狀不同」更精確: 上游買的是**觀察不要漏記**,
代價是把 skill 變成背景遙測; 我方的 `task-observer` 明文把「寫入需要使用者授權」當成設計的
第一條, 而強制檢查點會直接推翻它. 這是**目標分岔, 不是我們認為它錯** —— 事實上依上面那張
表, 它多半是對的.


### 兩份 reference 詳讀之後 (2026-08-28 補)

上一版說這兩份只掃了標題. 詳讀之後**它們不是排程流程與撰寫規範而已**, 裡面有兩條是本 repo
當天就踩到的失效, 都已採用:

| 上游規則 | 處置 | 依據 |
|---|---|---|
| **絕不用「對選填欄位做 grep」建工作佇列**: 先列出權威識別碼 (`### Observation N:` 標頭), 再逐項分類, 再**斷言兩個計數相等**; 差額就是沒有狀態的條目, 要浮出來 triage 而不是當成乾淨 | **採用** | 見下 |
| **relocation 的兩層驗證**: diff 出舊底本每一行 → `grep -F` 逐行精確比對新檔集合 → 未命中的用一段有辨識度的中段字串做實質比對再下結論 → 每檔字數 sanity check. 單用一層要嘛漏掉真損失, 要嘛對重排行誤報 | **採用** | 見下 |
| **登記成功才寫標記**: 排程註冊失敗時不得寫 `scheduler-registered.txt`, 否則「標記會永久壓掉 fallback 而檢討從來沒跑過」 | **佐證** | 本 repo 2026-08-28 在 `prompt-bundle-report` 上獨立踩到同一個形狀 (基準檔壞掉被當成「還沒有基準」, 重記一份然後安靜回 0 —— 哨兵把自己關掉). 兩邊都是**哨兵自我失效**, 我方已修 |
| **Pre-Flight Principle**: 有規則就要有一個交付前重讀規則並比對產出的驗證步驟 | **佐證 (同作者, 不算新票)** | 與該上游 `SKILL.md` 的強制寫入是同一個論證, 已計為一票 |
| **嵌入 skill 的指令必須先對真實資料跑過一次再存檔** —— 散文規則每次執行都會被重新詮釋, 嵌入指令則逐字, 無人看管, 永遠照跑, 而錯得微妙的指令每次重讀都像對的 (它給的例子: `git log -1 --format=%cI --reverse` 回傳的是**最新**的 commit, 因為 `-1` 在 `--reverse` 之前生效) | **已落地 (腳本本身), 當場補查了引用面** | 腳本由測試實跑 (`test_task_observer.py` 與 `test_ledger.py` 都是 subprocess 呼叫真檔). 上游問的是更窄的一問 —— **skill 正文裡那一行**對不對 —— 所以當場把 16 份 skill 正文的 `bash` 區塊逐條抽出, 對各自的 `--help` 比對旗標: **11 個呼叫, 0 個不符**. 沒有把這個做成常設檢查: 一次性驗過, 而下一次改動由既有的 subprocess 測試接手 |
| staging-only: 絕不直接寫 live skill, 即使目錄可寫; 這是安全性質不是檔案系統限制 | **已落地** | `task-observer` 的「Git checkout 為真相源, 絕不編輯 project-managed 副本」 |
| 交付前閘: staged `SKILL.md` body 裡每個 `references/` 路徑都要有檔案在 staged 集合裡 | **已落地, 機制不同** | 我方由 deployment manifest 加 parity 檢查涵蓋 |
| **持久化與執行環境是兩條獨立的軸** —— 知道狀態放哪不等於排程器搆得到它 | **佐證** | 我方 hook 與帳本同機, 屬上游三個 regime 的第三種; 這條目前不咬我方, 但它是我方沒有明說過的區分 |
| 「一次什麼都沒套用的檢討只是報告產生器」 | **佐證, 而且咬到第二輪的發現一** | 我方的量測面指紋 13 個戳章 12 個過期而且過期是設計常態 —— 那正是「報告產生器」. 見 [peer-harnesses](cross-upstream-synthesis.md#跨上游整合第二輪-2026-08-28-進行中) |

**兩條採用都落在 `.claude/skills/upstream-distillation/SKILL.md`** (repo-root dev-only, 不進
部署清單, 所以沒有字數預算問題), 接在既有的「Calibrate the probe」後面 —— 那一段講的是
「什麼都找不到的探針」, 而這兩條講的是它抓不到的那一種: **回傳一個看起來合理的子集**.

**採用它們的本機證據是同一天的三次失效**, 不是上游的權威:

- 時效性表的掃描把標頭用「內容比對」濾掉, 而三個資料列的內文也含那個字串 —— 報出 10 列,
  實際 13 列, 而且看起來很健康.
- 找壞掉錨點的 grep 輸出被截斷, 漏掉一個, 由連結檢查器補抓到.
- (歷史) `fnmatch` 讓涵蓋率斷言不可證偽, 整個 research 目錄悄悄進了稽核信封三週.

**relocation 那條當場對自己用了一次**: 2026-08-28 的日誌拆檔跑第一層, 舊底本 447 個非空行
在新的兩份檔案裡**全部精確命中, 0 個未匹配**. 拆檔本身因此驗過, 而不是只有「測試綠」.

### 還是沒有查的

`references/environments.md` (4,950 bytes) 沒有讀 —— 它講各平台的啟動設定, 而我方的啟動
由契約與 description 決定, 形狀不同. 上表最後一列原本是開著的問題, 已於同日查完並改成處置.

**那次查核本身值得記, 因為它當場示範了剛落地的規則.** 第一版探針對 `observation-log`
報出 **12 個旗標不存在**, 看起來像真的缺陷. 實際是探針錯了: 那支腳本用子指令,
頂層 `--help` 當然列不出 `add` 底下的旗標. 校準之後 (改成對子指令要 help) 是 0 個不符.
剛寫進 `upstream-distillation` 的那兩段講的正是這件事 —— 而它在寫下之後不到十分鐘就
逮到自己一次.
