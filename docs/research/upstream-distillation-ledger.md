# 蒸餾帳本: 上游每一節的去向

這份帳本記**逐節處置**. 到 2026-08-28 為止它只寫過一個上游, 而那是歷史造成的不是分工造成的
—— 其他上游的處置散在各自的文件裡 (speak-human-tw 有自己一份, cablate/baton 在
[peer-harnesses](peer-harnesses.md), fable-method 在 [trap-experiments](trap-experiments.md)),
只有 `rebelytics` 一個**哪裡都沒有**. 2026-08-28 的對應性檢查抓到那個洞, 補在本檔末節.

| 上游 | pin | 逐節處置在哪 |
|---|---|---|
| [mattpocock/skills](https://github.com/mattpocock/skills) | `6654f6b60cd9d5be8b54c6fafe44346dabeb3b76` (marketplace pin, 2026-09-05 解析; 前一個 `885e2ca4` 用了 08-17 到 09-05) | 本檔主體 (下方各 mattpocock 節) |
| [rebelytics/one-skill-to-rule-them-all](https://github.com/rebelytics/one-skill-to-rule-them-all) | `f4a95a180404bd4de35365da66849a243e3d07be` (`v3.1.0`, 2026-09-05 推進; 歷任 `281f1346` v2.0.0 → `9d1491b8` v3.0.0) | [08-28 v2.0.0 逐條](task-observer-upstream.md#rebelyticsone-skill-to-rule-them-all-逐條處置-2026-08-28), [08-31 3.0 逐條](task-observer-upstream.md#rebelytics-30-改版逐條-2026-08-31-上游朝我方的形狀走了過來), [09-05 3.1 逐條](task-observer-upstream.md#rebelytics-31-改版逐條-2026-09-05-上游在補儀器的守則-我方多半已有) |
| [Nanako0129/sepia](https://github.com/Nanako0129/sepia) | `0162048ac8123e675fb40028298d72245eff2acb` (head, 2026-09-05; 前一個 `4c8d782f` 2026-08-30; 沒有 ATTRIBUTION, 因為還沒有內容落進 `main/`) | [08-31 逐條](#nanako0129sepia-與其上游論文-storyscope-逐條處置-2026-08-31), [09-05 v0.7.0 重查](#sepia-v070-重查-2026-09-05-中文校準檔直接對上-readable-zh-tw) |

**沒標上游名的節講的都是 mattpocock/skills; sepia 有自己標了名的節; rebelytics 的逐條自 2026-09-05 起在 [task-observer-upstream](task-observer-upstream.md), 本檔只留每輪全掃的讀數表.**

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

## `rebelytics` 的逐條處置搬到 task-observer-upstream (2026-09-05 拆檔)

四節原樣搬走: 08-28 的 v2.0.0 逐條, 08-31 的 3.0 改版逐條與殘讀補完, 09-05 的 3.1 改版逐條, 現在在
[task-observer-upstream](task-observer-upstream.md). 理由: 本檔到 28,184 字, 過了 20,000 字的
單一責任守衛; 縫是主題 —— 那四節是唯一自成一條線的上游. 兩層驗證 (不含本段):

```text
舊底本 (本檔, 拆前)                  766 個非空行
對新的兩份檔案聯集精確比對            未命中 4 (全是改了跨檔連結或指向新檔的行, 逐行看過)
實質比對 (去連結後前 24 字)            未命中 0
字數                                  28,184 → 本檔 14,394 + 新檔 14,089
強制機制: 「推翻條件」字樣            12 → 12
```

每輪全掃的讀數表 (08-28, 08-31, 09-05) 留在本檔; 上表 pin 欄的連結已指向新檔.

## 2026-08-31 重查: 六個遠端全掃, 一個上游第一次真的動了來源檔

使用者指名 Headroom 有動, 順帶把有上游的內容全部重查一輪. `upstream-pin-report.py`
跑五個 ATTRIBUTION pin, 其餘用 PyPI/GitHub API 當場問. 讀數:

| 上游 | 讀數 | 處置 |
|---|---|---|
| `fable-method`, `cablate/baton` | pin current | 無事 |
| mattpocock/skills | 預設分支仍在 `6654f6b6` — 與 08-28 重查同位, 這次是真的沒動 | 無事 |
| speak-human-tw | +3 commits, touched 只有 `assets/` (1) | 又是機器人重畫星數圖, 第四輪; 來源檔沒動 |
| Deep Agents | 0.7.7→0.7.11, code 0.1.58→0.1.65, acp 0.0.10→0.0.11 | 版本表更新; 內容差異未讀 |
| Pilotfish | v1.3.10→**v1.4.1**: 變成原生 Claude Code Plugin (marketplace + fail-closed SessionStart 注入), 手動 cue 退場 | 質變, 完整拆解排進 peer-harness 輪 (pending-evidence) |
| Headroom | 0.36.1→**0.37.0** (五版) | 見下 |
| rebelytics | pin `281f1346` → head `510caad2`, **+35 commits, 四個來源檔全動** | 六個上游裡第一次: 見下節逐條 |
| eli5 | 兩個 API 路徑都查無 path commit | 本輪未查成, 保留 08-28 讀數 |

### Headroom 0.36.2–0.37.0

已釋出五版讀完 changelog: 多數是 proxy/整合修理. 對本部署值得記的: 0.36.4 又一條安全修
(`#3195` 對每條解析路徑驗證 caller-supplied upstream —— 0.36.1 才因為安全性釋出進過這張
帳), 0.37.0 給 WebSocket 握手加 `HEADROOM_PROXY_TOKEN` 強制 (`#3305`), 加了 session-aware
sidecar 壓縮與自限式 session 狀態.

**更正 (2026-08-31 當日, 升級後查證): 本節原本斷言四項大改「還不在任何釋出版裡」, 那是
錯的, 四項全部都在 0.37.0.** 原文的推理是: changelog 的 `Unreleased` 段列著 telemetry
改預設關閉的 opt-in, `#2085` 的平行 subagent prefix-freeze 污染修 (回報 ~4.4x
cache-creation 膨脹), proactive expansion 出處標籤, MCP 孤兒進程收割 —— 於是我把「它在
Unreleased 段」讀成「它還沒釋出」. 升級到 0.37.0 之後對**裝好的檔案**查, 四項逐一都在:

```text
telemetry/beacon.py       is_telemetry_enabled()  fail-closed, 只認 on/true/1/yes/enable
cache/prefix_tracker.py   resolve_tracker(), max_lineages_per_session = 32
ccr/context_tracker.py    <headroom_proactive_expansion> 標籤
ccr/mcp_server.py         _await_parent_death() 監看 ppid
install/supervisors.py    _bootstrap_with_retry(), install_supervisor 已在用
```

**教訓, 而且是本 repo 自己寫過的那一條**: 上游的段落標題是中介, 不是製品. 「在哪一段」
回答的是上游怎麼歸檔, 不是二進位裡有沒有; 要問「有沒有」就得問裝好的東西. 這和 sepia
那輪「論文本文沒讀, 只驗了摘要」是同一個洞的兩次現形 —— 差別只在這次可以當場問, 而我
沒問就寫了. 往後引用上游 changelog 的 `Unreleased` 段, 一律附一次對安裝版的查證, 或者
不寫版本歸屬.

另記: PyPI 的 repository URL 指 `chopratejas/headroom`, changelog 內鏈全指
`headroomlabs-ai/headroom`, 兩邊都解析得到 —— 引 issue 用後者.

## `Nanako0129/sepia` 與其上游論文 StoryScope: 逐條處置 (2026-08-31)

**為什麼進來.** 使用者指名. `sepia` 是一支 de-AI writing skill (MIT, Nanako Tsai), 分兩半:
小說側修敘事架構, 專業文書側給每種 venue 配規則檔. 專業側直接壓在本 repo 每天在寫的東西上
—— 回覆, 紀錄, 派工單, 研究文 —— 所以它是第六個上游, 而且是第一個「寫作方法」類的.

**查了什麼.** Pin `4c8d782f89a6518c0da6c24d5a466733db5ef7ab` (2026-08-30, 預設分支最後
merge). 讀的是位元組不是任何人的摘要:

| 上游檔案 | sha256 前 16 | bytes |
|---|---|---|
| `skills/sepia/SKILL.md` | `0518ec9f24b5ba1f` | 6733 |
| `references/professional-pass.md` | `6919f6fe242f3fc8` | 5723 |
| `references/domains/dev-replies.md` | `a0fc73ee75f65d7d` | 2537 |
| `references/domains/postmortems.md` | `04471baf7209dd3a` | 2564 |
| `references/domains/tickets.md` | `ea62da367c7139de` | 1725 |
| `references/domains/release-notes.md` | `8b2e98b81681341c` | 2005 |
| `references/domains/tech-articles.md` | `81f055467c11093d` | 2987 |
| `research/storyscope.md` | `10ce892bd00f0227` | 10534 |
| `research/sources.md` | `9b9f6bd2b6215354` | 8780 |

論文照規矩**獨立重抓**, 不信中介筆記: arXiv:2604.03136 (StoryScope, Russell et al., v6
2026-08-10) 的摘要數字與 `sepia` 自己的消化紀錄逐項對上 (61,608 篇, 304 特徵, 30 core,
narrative-only 93.2% macro-F1, 6-way 68.4%). 一處出入記在「沒有查的」.

**血緣警告, 先講.** 下表多數「已落地」的重合, 我方規則早於讀到 `sepia` (全域契約與
`readable-zh-tw` 都是 2026-07 起的), 所以不是從它來的; 但 `sepia` 這一側是不是讀過我方
的實踐才寫的, **查不到也沒查**. 依「收斂要先數血緣」: 下面每一條重合都只當**佐證**,
不當獨立收斂票, 直到血緣釐清.

### 逐條 (專業文書側, 可轉移的那一半)

| 上游規則 | 處置 | 依據 |
|---|---|---|
| venue corpus 定義目標聲音, 不是 skill 定義; 先讀 2-3 份該 venue 的人寫品 | **已落地** | 「寫得像周圍的 code」與 `readable-zh-tw` 的散文標準同形; 上游多給了「先取樣」這個動作 |
| checklist #1/#7: chatbot 殘渣與結論殘渣整類刪除 | **已落地** | 全域契約「no flattery, no preamble, no generic close」逐字同一類 |
| #2 密度: 一半長度說得完就是失敗; 長度 ∝ 利害 | **已落地** | 「conversation proportional」與密度三指標 (bytes/rule, rule count, filler ratio) |
| #4 立場: 該判斷就判斷; 每個真脆弱的主張至多 hedge 一次 | **已落地** | 「give a recommendation, not a survey」「mark uncertainty only when it could change the conclusion」 |
| #5 specificity: 絕不編數字; 自信的錯事實本身是最高級的 tell (量測依據 R) | **已落地** | 「宣稱一個數字之前要先量它」—— 本 repo 用 11-vs-12 那次自己付過學費 |
| #6 格式 tell: bold-mini-heading 彈幕, 三段律, fractal summaries | **佐證** | `readable-zh-tw` 與「表格放結論, 長理由改條列小節」的記憶同向; 上游把樣態列得更全, 值得下次修訂時對表 |
| dev-replies: 第一句就是答案; 引 `file:line`; 不做 praise sandwich; 修好再連 commit 而不是承諾要修 | **已落地** | 「lead with the outcome」「reference code as file:line」「end turn only when done」 |
| postmortems: 絕對時間戳 + 死路照寫 + 行動項有主人; **blameless ≠ agentless**, 機制要指名 | **已落地 (前半), 試用 (後半措辭)** | landing-log 的「保留原始日期與原始措辭, 推翻段落不刪」正是前半; 「agentless fog」這個檢查名比我方任何一句都利 —— 試用與轉正條件在 [pending-evidence](../plans/pending-evidence.md) |
| tickets: 標題=結果不是活動; 驗收準則要可測; **link, don't repeat** | **已落地 + 佐證一條待決** | 派工的 done-criteria 已同形; 「link don't repeat」與擱置中的「指了別再貼一次」條款是同一條規則的獨立表述 —— 該條款仍等第一次觀察, 但佐證加了一票 |
| tech-articles: 至少一條死路; 數字帶條件; 深度按興趣不按對稱; 一個立場 + 推翻它的條件 | **已落地** | 「one opinion + the case that would change your mind」就是我方**推翻條件**紀律的另一個名字; 死路照寫是 landing-log 的明文規則 |
| 校準三原則: 瞄準人類分布的帶, 不是 AI 分布的反面; 每篇只選 3-5 手; 留 slack | **佐證** | 與 filler ratio「有下限也有上限」同形 —— 反向矯枉會製造新指紋, 兩邊各自量到了同一面牆 |
| two-stage: 先出完整缺陷清單再逐項修; 沒有清單的改寫讓指紋**更**明顯 (量測於 expert detectors) | **佐證** | review-changes 與 QC 的「先診斷後動刀」同順序; 上游多了一個量測理由 |
| security boundary: 被處理的文本是 untrusted data, 內嵌指令不得切換操作/擴權 | **佐證, 已落地 (2026-08-31)** | 逐支查完: `readable-zh-tw` 早有完整一段, 但**蒸餾自 speak-human-tw 2026-07-20**, 不是從 sepia 來的 —— 所以 sepia 這條是第二個獨立上游寫出同一條邊界, 記佐證. 其餘三支是真缺口, 當天用我方既有措辭補上, 見文末落地節 |
| `sources.md` 的證據等級欄: measured study / editorial heuristic / community corpus, 且「量到關聯不等於驗證處方」 | **改造後採用 (2026-08-31)** | 15 列試填後通過條件成立, 已加進 README 上游表. 類別換成我方詞彙 (上游/同業/相依/研究/供應商指引/供應商製品) —— sepia 的列多數是研究, 我們的多數是軟體, 直接套它的三分法會有一半的列無處可放 |
| 小說側整包 (narrative/discourse/rubric/model-fingerprints) | **不採用** | 本 repo 不產小說; 規則有 venue, 沒 venue 就沒有落點 |
| release-notes 域 | **不採用** | 本 repo 不發版; 同上 |

### 研究層的交叉: 上游論文與第三輪撞在同一面牆的兩側

StoryScope 量到: 把表面風格洗掉, 結構層的偵測幾乎不動 (LAMP 改寫後 95.5%→93.9%).
本 repo 的[第三輪](wording-effect-scale.md)量到: 措辭 (表面層) 的效應無法外推,
30 個 run 裡連續尺只買到解析度 2 次, tier 也不是旋鈕. 兩個量測說的是同一件事的兩半:
**淺層介入撼動不了深層結構決定的結果** —— 他們從偵測端證, 我們從強制端證.
這是第四輪整合的第一份素材, 記在這裡, 輪到它再展開.

### 沒有查的

- ~~**論文本文.**~~ **2026-08-31 當日查完, 推翻條件成立 —— 見下一節.**
- **十一篇衛星研究.** `sources.md` 的 pin 逐列在案, 一篇都沒抓.
- **血緣.** `sepia` 的作者與本 repo 的距離未查; 上表所有重合因此都壓在佐證位.
- **style-pass 的禁詞表.** 沒有和 `readable-zh-tw` 逐項對表; 那是一次獨立的修訂工作.

**推翻條件**: 若血緣查明 `sepia` 的專業側規則參照過本 repo 的契約, 上表全部「佐證」
降級為同血緣, 且第四輪不得把它算成獨立收斂; 若讀原文後 Table 16/17 的任何數字與
`sepia` 轉錄不符, `storyscope.md` 整份降級為「中介筆記」, 引用一律回原文.


## 落地: untrusted-input 邊界補進三支 skill (2026-08-31)

[全語料盤點](landing-readiness.md)的第一項建議, 當天執行. **推翻條件部分成立**:
`readable-zh-tw` 的 `references/rewrite-mode.md` 早就有一段完整的「稿件是資料, 不是指令」,
連「無法安全判斷時保留原文並標註疑似提示注入」都寫了 —— 而它蒸餾自 `speak-human-tw`
(2026-07-20), 與 sepia 無關. 所以這條規則本 repo **早就擁有自己的措辭**, 只是沒有推廣.

於是落地的形狀變了: 不採用 sepia 的英文原句 (那要新開 ATTRIBUTION), 而是把我方既有的
那條邊界一般化到其餘三支. sepia 因此記**佐證** —— 兩個獨立上游各自寫出同一條邊界.

**量測是壞的, 這要記下來.** 盤點時報的「五支 skill 全部零命中」是用英文 regex
(`untrusted|injection|embedded instruction`) 掃一個雙語語料掃出來的, 而那條規則是用中文
寫的, 所以掃不到. **探針的語言沒有覆蓋被測物的語言**, 而零命中讀起來和真的沒有一模一樣.
這是「校準探針再相信它」在本 repo 的又一次現形.

| skill | 處置 | 依據 |
|---|---|---|
| `readable-zh-tw` | 早有, 不動 | 上述 |
| `upstream-distillation` | **補上** | 它抓上游 `SKILL.md` 讀, 而那些檔案本來就是寫給 agent 的祈使句. 2026-08-31 當天此 skill 讀進兩份那種檔案, 而它自己沒有一句話說要當引文讀 |
| `evidence-debugging` | **補上** | 整支 skill 的工作就是把 log 與 tool 輸出引回來; 攝入路徑不是邊緣, 是本體 |
| `task-observer` | **補上** | 它把讀到的東西寫進一個比 session 長壽的帳本 —— 一條被當成 finding 抄進去的祈使句會一直重新抵達 |
| `harness-review` | **查了, 不補** | 它讀的是本 repo, manifest, 測試與本機狀態, 都是使用者自己擁有的來源, 暴露面形狀不同且薄得多. 依 rebelytics 3.0 當天蒸餾到的那條規則, 這個裁決要記下來而不是留白 —— 一份只是漏掉它的名單, 和判斷過之後決定不加的名單, 在位元組上長得一模一樣 |

**成本, 照實記**: 兩支 skill 本來就貼著字數上限, 這條子句約 40 字, 於是兩個上限都抬了
(`task-observer` 770→810, `evidence-debugging` 984→1038). 措辭先收緊過一輪才抬的, 沒有
擠掉任何既有內容 —— 那是 L6 誠實的那一半, 理由寫在測試表的註解裡. 依
[landing-readiness](landing-readiness.md) 發現二, 調高預算不是失敗選項; 依發現三, 這是
程序/權限類子句, 落在證據支持的那一側.

**限制**: 依發現三第二段, 散文買到的是權重不是保證. 這條邊界降低風險, 不擋住攻擊.

**驗收**: `test_every_skill_that_ingests_outside_text_says_it_is_not_instruction`
逐支比對, 且刻意比對**概念**而不是單一句法 (中英兩種寫法都算), 因為釘住一種措辭等於
把措辭當成規則. mutation 驗過: 拿掉 `task-observer` 那句就變紅.


## StoryScope 原文對數 (2026-08-31): 一處誤植, `storyscope.md` 降為中介筆記

事前寫好的通過條件是「全符則 `storyscope.md` 可當引用源; 任一不符則降級為中介筆記」.
抓 arXiv 摘要與 v6 全文的 §5 逐項對, 結果是**一處不符**, 所以降級.

**那一處**: `sepia` 的模型指紋筆記把「夢境過多」記在 **Gemini** 名下, 並自己註明
「abstract 提及」. 而摘要的原句是 **"GPT over-indexes on dream sequences"**; §5 另外寫
Claude **avoids** dream sequences. 也就是說 `sepia` 把摘要自己那句話的主詞換掉了 ——
Claude「避免夢境」它抄對, 「過多」卻掛到了 Gemini 而不是 GPT. 這是可以只靠摘要就抓到的
出入, 而它在原筆記裡標的來源正是摘要.

**其餘對得上的部分照實記**, 因為降級不等於整份錯:

| 讀數 | 原文 | `sepia` 轉錄 |
|---|---|---|
| Core Only 二元 | 84.8 macro-F1, AUPRC .828 | 相同 |
| narrative-only 二元 | 93.2 F1 | 相同 |
| 稀有度百分位 | 0.71 對 0.49, Cohen's d = 0.83 | 相同 |
| 人類故事落在最稀有 10% | 24.7% | 相同 (未帶 AI 側的 7.1%) |
| Claude | 事件強度最平, 敘事聲音最均勻, reverent/continuist 62% 對 39–56%, 愛 epilogue, **避免夢境** | 相同 |
| GPT | gossip/rumor 64% 對 44–55%, 顛覆期待 41%, 遠距回顧, ensemble | 相同 |
| Gemini | 結局最乾淨, 長 denouement, 88% bleak | 相同 |
| DeepSeek | context 前置 | 相同 |
| Kimi | 指紋最少, 位於 generic center | 相同 |

**原文另有幾個 `sepia` 沒帶的數字**, 記下來供日後引用: Core Only 六向 46.5 macro-F1 /
46.8% 準確率; Core+FP (101 特徵) 91.1 F1 / .934; Full Narrative (257 特徵) 93.2 F1 /
.959; 最稀有 1% 是人類 3.0% 對 AI 0.6%; 人類版本在同一個 prompt 的六份裡被評為最稀有的
比例 **57.8%** (機率基準 16.7%); 六向逐類 F1 —— 人類 .89, Claude .77, GPT .73,
Gemini .60, DeepSeek .57, Kimi .55.

**處置**: `sepia/research/storyscope.md` 自此當**中介筆記**, 不當引用源. 要引 StoryScope
的任何數字, 引 arXiv:2604.03136v6 本身. 本 repo 目前唯一引用它的地方是
[ledger 的 sepia 節](#nanako0129sepia-與其上游論文-storyscope-逐條處置-2026-08-31)與
[cross-upstream-synthesis](cross-upstream-synthesis.md) 的研究層交叉, 兩處引的都是
「narrative-only 93.2%, 洗掉表面風格後 93.9%」這組, 已對過原文, 不受影響.

**仍然沒有查的**: Table 16 的 30 個逐特徵人類/AI 均值在 Appendix I, 這次的取得路徑拿不到
全文附錄, 所以那些數字 (Thematic Explicitness 3.28 對 3.94 之類) **仍然只有中介筆記一個
來源**. 引用它們要標明這件事, 或者先取得附錄. 另外 Krippendorff's α=0.90 與
human–model κ=0.84 也未驗.

## 2026-09-05 重查: 五個 pin 三個動, marketplace pin 第一次真的前進

使用者要求整輪更新上游來源. `upstream-pin-report.py` 跑五個 ATTRIBUTION pin; 沒有
ATTRIBUTION 的 (sepia, fable-method 已 current) 與同業/相依列用 GitHub 與 PyPI API 當場問;
client 注入區塊用本機 `prompt-bundle-report`. 讀數:

| 來源 | 讀數 | 處置 |
|---|---|---|
| mattpocock/skills | 預設分支 `3cca18b3` (對舊 pin +10); **marketplace catalog 現在釘 `6654f6b6`** (`anthropics/claude-plugins-official` 的 `.claude-plugin/marketplace.json`, catalog commit `46260264`, 2026-09-04) —— 08-17 以來第一次前進. 四個來源檔對舊 pin, 新 pin, head 三個 SHA 各跑一次 `upstream-recheck.sh`, 全 matches | pin 推進到 `6654f6b6`, 純記帳. 十個 commit 裡八個是 08-24 與 08-28 已逐條的 (`implement-spec`, `retro`, `grilling` 版面); 新的兩個只動 `scripts/link-skills.sh` 與 `CLAUDE.md` 一行, 無規則 |
| speak-human-tw | +9, `touched` 只有 `assets/` (1); 六檔在 `fa09500c` 全 matches | 第五輪機器人星數圖; pin 推進 (記帳), 逐次在 [readable-zh-tw-upstream](readable-zh-tw-upstream.md#2026-09-05-重查-九個-commit-全是星數圖-第五輪) |
| rebelytics | **`v3.1.0`** (tag `f4a95a18`, 2026-09-04); 對 `v3.0.0` +43 commit, 七個來源檔動六個, 另新增 `references/starter-principles.md` (296 行); head `2967fa5f` 只多 `CONTRIBUTING.md` | 逐條在[task-observer-upstream 的 3.1 節](task-observer-upstream.md#rebelytics-31-改版逐條-2026-09-05-上游在補儀器的守則-我方多半已有); pin 推進到 tag |
| sepia | **`v0.7.0`** (2026-09-04); 對 `4c8d782f` +86 commit, 31 檔; 九個來源檔動三個 (`SKILL.md`, `professional-pass.md`, `research/sources.md`), 五個 domain 檔與 `storyscope.md` 一個位元組沒動; 新 `references/languages/zh.md` | 逐條在[下節](#sepia-v070-重查-2026-09-05-中文校準檔直接對上-readable-zh-tw); 記錄的 pin 推進到 head (tag 之後 `sources.md` 又多一筆, 讀的是 head) |
| fable-method, cablate/baton | pin current | 無事 |
| Pilotfish | release 仍 `v1.4.1`; head `ea0d20bb` (+15, 08-27 到 08-28), **全是 `benchmarks/**/attempts.json` 的綁定** (dispatch positive controls, verifier paid summaries, compact policy full matrix, cue-free TUI) 加 `tests/test_policy.py` +3,855 行 | 未讀內容; 這是同業把自己的嘗試 (含負結果) 綁成資料檔, 排 peer-harness 輪 (計畫 P8) |
| pilotfish-codex | head `74ad9a79` (2026-08-11) 未動; tag `v1.7.2` (`b2019f4a`) 存在但無 release | 無事 |
| Deep Agents | `deepagents` 0.7.11→0.7.13 (09-02), `deepagents-code` 0.1.65→0.1.66 (09-03), `deepagents-acp` 0.0.11 未動 | 版本表更新; 內容差異第三輪未讀 |
| Headroom | 0.37.0 未動 | 無事 |
| eli5 | 根目錄 `eli5` 最後 commit 仍 `863e70dc` | 無事 (先用 `plugins/eli5` 查了一次空, 又踩 08-31 修過的坑, 改查根目錄才對) |
| Claude Code client | **2.1.261**: `opus_5_prompt_bundle` 的兩行文字**不在**, `tengu_heron_brook` 無, `tengu_fennel_godwit=false`, 「section not active on this build」. weekly-integrity 開場報的, 前一狀態自 08-28 (2.1.247) 持續到今天 | 通貨表列更新, 08-28 節補一段; 對 2.1.247 量的結果其量測面已過期 → 計畫 P10 |

**方法上的更正, 要記.** 08-28 兩份 mattpocock ATTRIBUTION 寫「pin 記的是 marketplace 送出什麼,
這裡沒裝 plugin 解析不了」—— 錯. catalog 是公開檔, 08-14 研究日就是從它讀的 (見
[mattpocock-skills-integration](mattpocock-skills-integration.md) 的來源清單), 後來兩輪忘了.
三輪「pin 沒動」的結論不受影響 (來源檔 blob 全程相同), 但這句話讓 pin 比事實落後了兩輪,
而且把一件可查的事登記成不可查. 這一輪的 pin 是從 raw 檔裡 `mattpocock-skills` 條目的
`source.sha` 讀出來的; 下次照做.

**查了什麼.** 五個 pin 的 compare (commit 與檔案清單); mattpocock 四檔對三個 SHA 的雜湊;
speak-human-tw 六檔對新 SHA 的雜湊; rebelytics 八個來源檔對 tag 與 head 的雜湊 (全同);
sepia 十個來源檔對 tag 與 head 的雜湊 (`sources.md` 不同, 其餘同); 三個上游的逐檔 diff 全文
(rebelytics: SKILL.md 410 行 diff, 五個 reference 共 948 行 diff, starter-principles 296 行全文,
三個 script diff; sepia: SKILL.md, professional-pass, sources.md 三個 diff 與 zh.md 全文);
marketplace catalog 的 raw 檔; Pilotfish 與 pilotfish-codex 的 tag/release/head; 四個 PyPI 版本;
本機 `prompt-bundle-report`.

**沒有查的.** AA Index (第四輪未查); Deep Agents 三個 package 的內容差異; Pilotfish 十五個
commit 的 attempts 內容; sepia 的 `model-fingerprints.md` (+97), `style-pass.md` §5 本文,
`research/rhythm-syntax.md`, `voices/`, `evals/` 的 grader 本文 (只讀了檔名與行數);
rebelytics 的 `signals.md` (未動, 不必讀); rebelytics 血緣 (仍未查, 08-31 的推翻條件維持).

## `sepia` v0.7.0 重查 (2026-09-05): 中文校準檔直接對上 readable-zh-tw

`4c8d782f` (2026-08-30) → head `0162048ac8123e675fb40028298d72245eff2acb` (2026-09-05); tag `v0.7.0` = `a0a374014141d929edec356fb86a5191d9eae6f7`
(2026-09-04), 與 head 只差 `research/sources.md` 一筆 (09-05 加的 `WAHI-JUDGE-2026`), 其餘九個來源檔
tag 與 head 全同. +86 commit, 31 檔; 四個版本 (0.4.0, 0.4.1, 0.5.0, 0.6.0, 0.7.0) 五天內出完. 08-31
登記的九個來源檔動了三個, 五個 domain 檔與 `storyscope.md` 一個位元組沒動; 新增一個與我方直接相關的
來源檔. 新位元組 (head):

| 上游檔案 | sha256 前 16 | bytes |
|---|---|---|
| `skills/sepia/SKILL.md` | `a9d177898782f6bb` | 9529 |
| `references/professional-pass.md` | `395f795e3af35bc1` | 6627 |
| `research/sources.md` | `112de5d4c887bda4` (tag `4a3443d499e851d1`) | 32,573 (tag) |
| `references/languages/zh.md (新)` | `5e145cc8f20d6b78` | 5976 |

其餘六檔雜湊同 08-31 表. pin 記在 [research README 的上游表](README.md#時效性基準); sepia 仍沒有
ATTRIBUTION, 因為沒有內容落進 `main/` —— P4 落地那天要補一份, 因為 `zh.md` 的形狀會進 `patterns.md`.

**主事件: 上游替中文做了一份「哪些 AI 痕跡在中文裡長什麼樣」的校準檔, 而且自己畫了證據邊界.**
數字來自一個語料 (HC3-Chinese, 簡中, 2023 年的 ChatGPT), 上游明寫「每個數字都是觀察過一次的方向,
不是校準常數」. 我方的規矩是方法可借數字不可借, 這裡連上游都這麼說, 所以只借形狀.

| 上游新規則 | 處置 | 依據 |
|---|---|---|
| 每條非小說路線都走句子節奏檢查 (`style-pass.md` §5), professional-pass #9 改成「量」 | **佐證** | `patterns.md` 與 `humanize.md` 已有句長變化; §5 本文未讀, 數字不借 |
| **中文校準檔 `zh.md`**: 連詞堆疊 (和/以及/並且/同時/此外/因此/然而 跨子句), 說明文裡的第二人稱 (你會發現/您可以), **雙音節動詞贅語** (進行討論/加以說明/予以處理/做出決定 → 動詞本身), 句長平坦; 該回補的: 語氣詞少量, 單音節動詞形容詞, 主語省略; 編輯啟發 (不是…而是, 名詞化 ○○性/○○感/○○化, 三段律, 其實/事實上 開段, 引號裡的抽象詞); **不是訊號**: 標點密度, 段落數 (ChatGPT 反而分更多段), 詞頻, 大陸用語 (是 venue 的語域錯配, 不是 AI 痕跡) | **改造後採用 → 計畫 P4 (只借形狀); 2026-09-05 已落地, 併進 patterns.md 第 10, 15, 19 條與「不是痕跡」一行** | 查了 `readable-zh-tw` 六個檔: 已有 不是…而是 (patterns, protected-list), 其實 (四處), 語氣詞 (taiwan-localization), 句長 (patterns, humanize), 連接詞 (patterns), 三段律 (三處); **沒有** 進行/加以/予以 動詞贅語, 說明文第二人稱, 名詞化, 「事實上」開段 —— 四個形狀. 「大陸用語是語域不是 AI 痕跡」與我方把它歸在台灣在地化 (可讀性) 而非去 AI 味, 同一裁決 |
| **模型身分**: author 與 executor 分開解析, 各自 family + version 或 unknown; prose layer 依 release 是 operative 還是 prior; 「絕不從文章推模型」(六向歸因是 304 特徵上 68.4% macro-F1 的分類器, 閱讀不是那個分類器) | **不採用 (機制), 佐證 (最後一句)** | `readable-zh-tw` 不做模型歸因. executor 端的 Fable 5.1 prose layer 對我方自己的輸出是相關的, 但證據類別是 vendor guidance (unmeasured) → 計畫 P11 只讀不採 |
| Voice fit, voice skill 疊合, Hemingway profile | **不採用** | 小說側, 無 venue |
| **密度雙向**: 「砍到一半長度說得完」之外, 砍掉必要的 caveat 或下一步的精簡回答也算失敗 | **已落地, 佐證+1** | 契約「對話按比例, 要求的產物要完整」正是雙向; 上游多了「caveat 與下一步」兩個具體物 |
| 版面痕跡: **沒有這些不是人寫的證據**, 模型多用少用哪種版面隨 release 變 | **佐證** | wording-effect-scale「結果要註明量測面」; 也證明我方版面規則是可讀性規則, 不是偵測規則 |
| 語域漂移守則: 改寫不得比原文更促銷 | **佐證** | 08-31 已收「校準三原則」; `readable-zh-tw` 的「不加個人風格」 |
| review 報告加 Model / Prose layer / Style scan 三行 | **不適用** | |
| `sources.md` 新增: 節奏與句法一節 (十餘篇量測研究, 含兩篇中文 CCL 論文); **「Consulted」表** —— 查過但沒有可用數字的來源, 記下來免得下次再抓流傳的數字 (例: ResearchGate 上掛在某論文名下的離散度數字, 論文裡沒有); vendor prompting guides (Fable 5.1, GPT-5.6, Opus 5…) 標 vendor guidance (unmeasured); `WAHI-JUDGE-2026` 「LLM-as-a-Judge 不是 oracle, 自我改進 agent 需要確定性守衛」標 engineering report (production observation, not controlled) | **佐證 (三件); 「Consulted」表改造後採用 → 計畫 P12** | 「查過但不能用」是我方「沒有查的」的另一半 —— 我方記沒查的, 上游記查了但沒用的, 兩個都在防同一種重工; WAHI 那篇與執行軸同向但類別不夠格加票 |
| `evals/deaify-release-note`: CI 裡的行為 eval, 三個 grader (skill-fired, reads-human, no-slop-markers) | **佐證 → 計畫 P11b** | `skill-fired` 就是我方 lifecycle-replay 量「skill 有沒有被叫」那一半; `readable-zh-tw` 目前沒有 eval (`evals/` 只有 replay, traps, scripts), 形狀可借 |
| `scripts/check_versions.py`: 宣告版本的 manifest 要一致; 拼法變體是無效不是隱形; 重複鍵是無效不是先者勝; 「一個正典鍵文法關掉整類拼法」 | **佐證** | 與 test_deployment 對 manifest 的態度同向; 沒有版本 manifest, 不採 |
| Star History 轉址修, zh-CN README, issue-first policy, security reporting | **不適用** | |

**P11a 讀了 (2026-09-05 同日): Fable 5.1 的 prose layer.** `model-fingerprints.md` 給 executor 端
三條供應商自述的預設: 造作的散文 (有直述可用時仍用比喻與花腔, 「a dial worth turning」代替
「a parameter worth varying」); 比 Fable 5 更密 (句長, 段落少); 比早期 Claude 少粗體, 少標題,
少列表 —— 並註明「稀疏版面不是人寫的證據, 不要加反向的版面規則來補償」. 類別 vendor guidance
(unmeasured), 上游自己標的. 對我方的意義: 本 repo 的回覆就是這個模型寫的; `readable-zh-tw` 第 17,
18 條 (說教式深度腔, 金句公式) 抓的正是比喻代直述的中文形狀, 已涵蓋, 不加規則. **P11b 的決定**:
`readable-zh-tw` 要有 eval, 形狀借 sepia 三 grader (skill-fired / reads-human / no-slop-markers),
與下一個 replay 批次一起開 —— 觸發是那個批次的事前登記, 不在本輪.

### 沒有查的 (本節)

- `model-fingerprints.md` 除 Fable 5.1 prose layer 以外的部分 (那一段 09-05 同日讀了, 見上); `style-pass.md` §5 本文; `rhythm-syntax.md`;
  `voices/`; `evals/` 三個 grader 的本文 (只讀了檔名與行數); 兩篇 CCL 論文本身 (上游的摘錄有引用,
  我方沒開原文).
- 論文 StoryScope 本文與血緣, 同 08-31.

**推翻條件**: 若 P4 落地後 `readable-zh-tw` 的那四個形狀在本機語料上 (`evals/**/runs/` 的舊名產物,
或 P11b 的 eval) 一次都不命中, 就回到 `patterns.md` 拿掉, 因為那是簡中 2023 的形狀不一定跨到繁中 2026;
上游自己的邊界一節就是這麼寫的.
