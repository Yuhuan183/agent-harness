# Engineering workflow 蒸餾實作計畫

狀態: **完成**. 兩個蒸餾 skill 已出貨並部署.
行為驗收量不出效果, 原因寫在下面; 後續判斷交給 `task-observer` 在真實工作裡累積.

最後更新: 2026-08-19
建立日期: 2026-08-14
研究依據: [Matt Pocock skills 導入研究](../research/mattpocock-skills-integration.md)

本文保留**判準, 決定與待辦**. 逐階段的施工紀錄 (M0–M5 的步驟, 各批的事前登記與逐批結果)
已於 2026-08-19 刪除, 因為實作完成而那些內容有自己的 owner:

| 找什麼 | 去哪 |
|---|---|
| 七批 75 runs 的登記, 結果與指紋 | [evals/replay/README.md](../../evals/replay/README.md) |
| 上游每一節蒸餾到哪, 捨棄了什麼 | [upstream-distillation-ledger](../research/upstream-distillation-ledger.md) |
| 兩個 skill 的實際流程與停止條件 | 各自的 `SKILL.md` 與 `references/tuning.md` |
| 現行預算數值 | `main/claude/tests/test_contracts.py` |

## 最終結果

### 出貨了什麼

| Skill | 來源 | 兩端 |
|---|---|---|
| `evidence-debugging` | 蒸餾自上游 `diagnosing-bugs` | 逐位元組一致 |
| `test-first-change` | 蒸餾自上游 `tdd` | 逐位元組一致 |

兩者都從 `main/.agents/skills/` 單一來源以整目錄 symlink 部署到兩個 provider,
`INSTALLED.txt`, `deployment-manifest.tsv`, census 與預算都涵蓋.

### 可以說與不可以說的

- **可以說**: 兩個 skill 蓋好了, 部署正確, 兩端逐位元組一致, 內容經過逐段 attribution 覆核;
- **可以說**: 常駐成本已量 —— 詳見[常駐盤點](../research/resident-context-options.md);
- **不可以說**: 它們讓結果變好. 沒有證據;
- **不可以說**: 它們沒用. 同樣沒有證據 —— 從來沒做出一個需要它們的題目.

### 三個假設都被推翻

| # | 假設 | 檢驗 | 結果 |
|---|---|---|---|
| 1 | 觸發清單全英文, 所以中文問法叫不動 | 加中文詞, 部署, 重跑 10 次 | 0/5 → **0/5** |
| 2 | 格子太鈍 (錯答案會自己承認) | 拿掉那句重做一格 `e6` | **5/5**, 更容易 |
| 3 | 被近似的 `debug-issue` 搶走 | 移除它重跑 5 次 | **0/5** |

三種情況下模型都把事情做對了.

### 真正卡住的是前提

原本的驗收邏輯是「沒有 skill 會做錯 → 有 skill 會做對」. **第一步做不出來.**
三輪嘗試裡每一個「做錯」查到最後都是環境擋住了指令, 不是模型的判斷. 引用任何比率時,
`commands_denied` 必須同時在視野內.

### skill 很少被自主選中, 而且不是我們獨有

40 個 run 的紀錄: 排除強制注入後, 35 次自主機會裡只有 **5 次**載入任何 skill
(`evidence-ladder` 3, `evidence-debugging` 2). 那台機器上 49 個 skill, **只有這兩個**曾被
自主選中過; `debug-issue` 與其餘 46 個一次都沒有.

所以不是「我們的 skill 被忽略」, 是這類任務上模型本來就很少去拿 skill.

## 待辦

| # | 項目 | 判準 / 下一步 |
|---|---|---|
| 1 | skill 效用判斷 | 由 `task-observer` 在真實工作裡累積, 三條判準見下方〈驗收路線〉 |
| 2 | ~~s10 的變異臂已經不是單一變因~~ | **2026-08-19 已修**: 三個臂改由 `build.py` 從 pristine 減去宣告的 lever 產生, 不匹配即硬失敗, 並納入既有的 `--check`. 舊結果列仍不可比 (當時是六份描述, 現在九份), 要用就重新量 |
| 3 | 常駐預算只覆蓋不到兩成 | 已量並已記, 歸屬移到[常駐盤點](../research/resident-context-options.md); repo 側能做的只有維持自己那份紀律 |
| 4 | `openai.yaml` 與 `description` 的語意漂移 | 已擋住改名 (目錄 / frontmatter `name` / `default_prompt` 三處一致), 語意仍靠 review. 沒有便宜的機械做法, 不假裝關掉 |

## 非目標

- 不複製完整 25-skill catalog.
- 不新增 router skill 或重造 `ask-matt`.
- 不導入自動更新器.
- 不新增 `CONTEXT.md`, 根目錄 `AGENTS.md` / `CLAUDE.md` 或 `docs/agents/*`.
- 不建立 GitHub issue, label, project 或其他外部 tracker 狀態.
- 不改 main session 的 model, effort, provider routing 或 dispatch quota.
- 不做 `change-shaping`, `change-review`, triage, wayfinder 或 wizard (M6 判定見下).
- 不 deploy, commit, push 或發 PR, 除非使用者另行授權.

## 設計原則

### 1. 一份 portable workflow, 一份 local tuning

每個 skill 的 `SKILL.md` 只保存必要流程與停止條件; agent-harness-specific 行為放
`references/tuning.md`. 這使上游重查時可以回答: 上游方法改了什麼? portable workflow 是否
需要跟進? local tuning 是否仍成立? 不能以三方 merge 自動回答這三題, 也不能讓更新工具覆寫 tuning.

### 2. Skill 不重新擁有 main contract

Skill 可以把既有規則轉成領域內的具體 stop, 但不能重複整份 global contract. 必要 pointer 應短
而可驗證: dispatch going ahead → load existing dispatch skill; diagnosis-only → no mutation;
external write/commit → require separate authority; exact verification → report failed or
skipped checks.

### 3. Portable core 不依賴 optional tools

`debug-issue`, AST graph, browser, GitHub connector 或其他 machine-local capability 可以加速,
但不得成為正確性前提. 沒有這些工具時, skill 仍可用 source, tests, logs 和 smallest probe 完成工作.

### 4. Tuning 是明示 policy, 不是 fork 雜訊

初始 tuning 來源只有: global working contract; agent-harness 已驗證的 review/deployment 方法;
使用者本次核准的蒸餾方向; 之後經明確同意記錄並 actioned 的 task-observer observations.
不得把單次偶發偏好直接永久化.

### 5. Tuning 變更協定

`references/tuning.md` 由 agent-harness 擁有, 但不能覆寫更高優先序的 system/developer
instruction, 當次使用者要求或 global contract. 每次新增或調整 tuning 都依下列流程:

1. 以一個應觸發案例和一個不應觸發案例描述想改變的行為.
2. 分類 ownership: 跨 repo 都成立的工程方法進 `SKILL.md`; agent-harness 的語言, 授權, 派工,
   驗證與輸出偏好進 `references/tuning.md`; 單次任務偏好不持久化.
3. 若 trigger 改變, 同步更新 `SKILL.md` frontmatter 的 `description` 與 `agents/openai.yaml`;
   body 內不另藏 invocation policy.
4. 先新增能反駁舊行為的 trap 或 fixture, 再修改 repo source. 不直接編修 HOME copy.
5. 跑 skill validation, focused behavior traps, contract tests, prompt census 與 deployment dry-run.
6. 以 `accepted`, `rejected`, `needs-more-evidence` 記錄結果; 需要 deploy 時另取明確授權.

上游更新不得自動改寫這一層.

## 上游相依的處置

2026-08-17 精讀 pin `068b6e0` 後確定的四項相依 (2026-08-21 重新溯源到 pin `885e2ca`, 上游那 12 個 commit 只動標點, 這四項的依據未變). **每一項都要有明文處置**, 不能只把上游那行
刪掉留下空洞 — 空洞會在蒸餾版裡變成沒有 owner 的假設
([研究](../research/mattpocock-skills-integration.md#第一批兩個-skill-的原始碼精讀)).

| 上游相依 | 本專案承接者 | 判準 |
|---|---|---|
| `CONTEXT.md` + ADR | `AGENTS.md` 與 [architecture.md](../architecture/architecture.md) | 蒸餾版指向既有 owner; 不得建立 `CONTEXT.md`, `docs/adr/*` 或任何新的根文件 |
| `codebase-design` skill (`tdd` 取 seam 語彙) | 蒸餾版自帶最小定義 | seam = 可觀察行為的公開邊界. 一句話帶完, 不留跨 skill 指標 |
| `tests.md` / `mocking.md` (TypeScript + Jest 範例) | 自寫等價範例 | 概念移植, **範例重寫**. 本 repo 的測試面是 Python `unittest`, shell, 與 markdown 契約斷言; 直接翻譯 Jest 範例會教出這裡不存在的習慣 |
| `scripts/hitl-loop.template.sh` (feedback loop 第 10 級) | **移除該級** | 本 repo 的驗證面沒有「必須有人點擊」的情境. 留一個未實作的指標比沒有更糟 |

## Attribution contract

每份 `ATTRIBUTION.md` 記錄: 上游 repo; reviewed release; **當下解析出來的**完整 commit SHA
(不是計畫裡凍結的那一個 —— 研究日是 `8b78b53`, 動手日已是 `068b6e0`, 而期間 release tag 與
plugin version 都沒動, 一個凍結的 SHA 會安靜地變成假的); 用到的上游 skill; 內容屬概念重寫
還是 substantial portion; MIT notice. 帶 substantial portion 時附 MIT 全文.

分類寫錯的方向只有一種要緊: **把 substantial portion 說成概念重寫**. 不確定時歸到前者.

### 兩個預測都偏向錯的那一邊

| Skill | 預測 | 實際寫下的 | 差在哪 |
|---|---|---|---|
| `evidence-debugging` | 一段近乎逐字 | **兩段** (進場判準 + redaction) | redaction 那節與閘一樣接近逐字, 初版列在「本專案新增」旁邊, review 才改回來 |
| `test-first-change` | 純 concept 重寫 | **兩段** (不可能失敗的斷言前兩類 + mock 邊界) | 「38 行索引」是對的, 但實質在 `tests.md` 與 `mocking.md`, 而那兩份的分類邊界被採用了 |

推論不是「以後預測要保守一點」, 而是**這種預測本來就不該當結論用**: 兩次都是在寫
`ATTRIBUTION.md` 逐段比對時才算清楚的. gate 認的是逐段那次.

逐段比對本身有一個機械檢查涵蓋不到的縫: 它只會檢查**已經列出來的**條目. 因此 recheck 段明寫
「re-classify every section, not only the ones already listed」, 這是唯一能防那個縫的東西,
而它是人做的.

## Invocation policy

Claude frontmatter 與 Codex metadata 必須表達同一套政策. 開放隱式呼叫前, 至少要有這些
false-positive 檢查:

- 「解釋這個測試在做什麼」不得叫起 `test-first-change`;
- 「review 這個失敗的測試」不得授權修復;
- 「診斷 CI 為什麼失敗」叫起診斷但不得改碼;
- 「先寫測試再修這個 regression」授權完整的診斷 + test-first 路徑.

若 false positive 無法以機械或可靠的觸發評估設限, 第一版設 `allow_implicit_invocation: false`,
觀察期內要求明示呼叫. 三個 skill 目前都是 false.

**Codex 側的使用細節**: `$name` 要放在**句首**. 寫成「Use $name. …」叫不動 —— 這是實測出來的,
第一次探測差點因此被報成「skill 在 Codex 上不能用」的嚴重缺陷, 是對照組 (`$readable-zh-tw`
同樣句式) 擋下來的.

## 兩個 skill 的分工

| 情況 | 誰 |
|---|---|
| 症狀已知, 原因不明 | `evidence-debugging` |
| 要改的行為已知 (含已診斷完的修復) | `test-first-change` |
| 只要求解釋或評估 | 都不是 |

`test-first-change` 的 `description` 直接點名 `evidence-debugging`, 這是刻意的: 不點名時兩者
只能靠語感分, 而「fix」兩邊都寫著. 代價是可攜層出現一個 sibling skill 名 —— 接受, 因為拿掉它
就沒有任何機制在描述層做這個區分.

與機器上的 `evidence-ladder` 有一條規則重疊而不牴觸, 判定不合併; 決定記在
[orchestration-history](orchestration-history.md) 的 2026-08-19 那筆.

## 新 skill 的建立基準

新 skill 要成立, 下列每一條都要有機械檢查:

| 判準 | 現有機制 |
|---|---|
| frontmatter 只有 `name` 與 `description`, 觸發語全寫在 `description` | `test_contracts.py` 解析 frontmatter |
| name + description 計入常駐預算 | `test_resident_skill_metadata_stays_within_budget`, CJK-aware 計字 |
| prompt census 記到 `kind: skill-metadata` | `scripts/prompt-surface-census.py --check` |
| Claude 與 Codex 解析到**同一份** `SKILL.md` | symlink 結構 + deployment 測試 |
| `INSTALLED.txt` 有 owner, `deployment-manifest.tsv` 兩個 surface 各一列 | `sync.sh` 與 weekly-integrity |
| `agents/openai.yaml` 的識別與 `description` 不漂移 | `test_every_shared_skill_states_the_same_identity_on_both_surfaces` (只擋改名, 語意靠 review) |
| body 長度與 reference 分層 | per-document 字數上限 |
| 出現在既有的 README 索引裡 | `test_every_shared_skill_appears_in_the_readme_that_indexes_its_peers` |
| 不新增 per-skill README / install guide / changelog | 慣例, 靠 review |

外部格式檢查可以跑, 綠不代表通過, 紅則直接修:

```bash
uv run --with pyyaml --no-project python \
  ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py main/.agents/skills/<name>
```

## 量測面的建立規則

### fixture 從失效分布長出來, 不是從最近一次痛的事

把 fixture 掛在最近一次事件上是**可得性偏誤**: 真實不等於有代表性, 而用一次事件當整套 fixture
的基礎, 正是本 repo 在別的載體上一直在防的 n=1 推廣. 改從已記錄的失效分布取樣.

### marker 不能掛在正確答案會碰的東西上

建格子的過程中同一個錯犯了**三次**: reach marker 掛在「該被改的那個檔」上, 於是把**最誘人的
錯答案**判成 invalid 而不是 incorrect. 三次都是跑閘才發現, 不是讀 grader 發現的.

這條**沒有機械化檢查**, 因為需要判斷. 所以它是新增格子時的固定檢查項:

1. 寫下這一格**最誘人的錯答案**是什麼 (不是最笨的, 是最像對的那個).
2. 問: 那個錯答案會不會被 marker 判成 **invalid**? 會, 就是 marker 錯了 —— 它正在藏這一格
   存在的理由.
3. marker 應該只問「有沒有動手 / 有沒有產出」, 判對錯交給 `correct`.
4. 建構那個錯答案的 workdir 跑一次閘, 確認它落在 **incorrect**.

### 兩件明文不在涵蓋範圍

| 沒做 | 理由 |
|---|---|
| 自動 commit / push / issue | replay 的 workdir 不是 git repo, 那一格量到的是 sandbox 不是契約. 這條斷言留在靜態 contract tests |
| 「一次只問一個精確問題」 | 想不出不脆弱的判準 —— 能想到的都得靠散文比對, 而這個 suite 沒有一格由 regex 判決 |

## 驗收路線改走 task-observer (2026-08-17 決定)

replay 量不出來的原因是它需要一個「模型會做錯」的題目, 而刻意造出來的題目量到的也不是真實
情況. 所以改成在**真實工作**裡觀察.

### 先講它抓得到什麼, 抓不到什麼

`task-observer` 的觸發條件是「**skill 協助過的**工作收到不滿或修正要求」. 我們的問題是
「該用而沒用」—— **那不是它現在的觸發面**. 不改它的 description (那要付常駐成本, 而且改一個
已部署 skill 的行為需要它自己的理由). 代價照實記: 這條路線抓得到「用了但不好」, 抓不到
「沒用而該用」, 除非那次摩擦的教訓本身指向方法.

### 判準 (先寫, 之後不改口)

- **三筆以上**觀察指名這兩個 skill 之一 —— 那是它們有負載的證據;
- **三筆以上**摩擦的教訓落在它們的守備範圍, 而它們沒有被載入 —— 那是觸發面的證據,
  而且是 replay 造不出來的那種;
- **連續一個月的真實使用沒有任何一筆指向它們** —— 那是「不是這台機器的瓶頸」的弱證據,
  屆時討論要不要退役, 而不是繼續加測.

不設時程, 因為證據來自實際遇到什麼, 不來自排程.

## M6 — `change-shaping`: 決定不做 (2026-08-17)

判定不新增. 理由是查出來的, 不是預算考量: 上游前半段 (`grill-with-docs` → `to-spec` →
`to-tickets`) 扣掉本 repo 已經有的, 一條新規則都不剩.

| 候選規則 | 現況 |
|---|---|
| 不問 repo 已經回答的事 | **已有** — `evidence-debugging` 的 tuning |
| 一次只問一個阻斷問題 | **已有** — 兩個 skill 各一處 |
| 外部寫入要明確授權 | **已有** — 兩個 skill 的 tuning 與全域契約 |
| 計畫寫在本地可核的地方 | **已有** — `docs/plans/` |
| 垂直切片 | **上游 `tdd` 本來就有, 我們漏掉了** |

最後一列 2026-08-17 更正: 原本寫「垂直切片是 `change-shaping` 唯一會帶來的新東西」. 重新抓
上游比對後發現它就寫在 `tdd` 的反模式一節 —— 也就是**已經蒸餾過的那個 skill** —— 而第一次
蒸餾只留了否定面, 把正面規則丟掉了. 已補回 `test-first-change` 的 Then 步驟 3.

`to-tickets` 的後半段假設有 issue tracker 可寫, 而本計畫的非目標明寫不依賴任何 tracker.

## Upstream recheck workflow

流程由 [upstream-distillation](../../.agents/skills/upstream-distillation/SKILL.md) (dev-only)
擁有, 這裡不再複述 —— 同一份步驟寫兩處會各自漂移.

有偵測器, 沒有自動套用器: [`scripts/upstream-pin-report.py`](../../scripts/upstream-pin-report.py)
由各 `ATTRIBUTION.md` 推導出上游清單, 回答「有沒有人動了」, 但要不要跟進由人讀 diff 決定.
本計畫在這件事上只留一條約束: **pin 只在選定的 diff 被審過之後才前進, 不因為跑過檢查而前進.**

## Rollback

1. Revert source changes, or remove the skill from source, inventory, provider surfaces and
   manifest in one reviewed change.
2. Run full preflight and dry-run.
3. Apply through `scripts/sync.sh --apply` only with deployment authority.
4. Verify managed files retired while unrelated third-party skill directories remain.

不要手動刪 HOME 的 skill 目錄; 受管部署狀態擁有退役, 而機器上不相干的 skill 必須保留.
