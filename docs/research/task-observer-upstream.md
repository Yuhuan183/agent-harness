# `task-observer` 的上游: rebelytics/one-skill-to-rule-them-all, 逐版逐條

2026-09-05 從[蒸餾帳本](upstream-distillation-ledger.md)拆出來: 帳本過了 20,000 字的單一責任守衛
(`test_the_human_tree_has_a_sprawl_guard_not_a_budget`), 而 rebelytics 四節是它裡面唯一自成一條線的
主題. 四節**原樣搬**, 只把指回帳本的連結改成跨檔; 每輪全掃的讀數表 (08-28, 08-31, 09-05) 留在帳本.
pin 與授權在 `main/.agents/skills/task-observer/ATTRIBUTION.md`; 落地排程在
[升級計畫](../plans/upgrade-plan-2026-09.md); 等待在 [pending-evidence](../plans/pending-evidence.md).

| 上游版本 | pin | 逐條在 |
|---|---|---|
| `v2.0.0` | `281f13466cd3a73e9ebc9d210907748e1941a3dd` | [2026-08-28](#rebelyticsone-skill-to-rule-them-all-逐條處置-2026-08-28) |
| `v3.0.0` | `9d1491b895c4f8f04f04977f74faad0f342c8b0c` | [2026-08-31 改版逐條](#rebelytics-30-改版逐條-2026-08-31-上游朝我方的形狀走了過來), [殘讀補完](#rebelytics-30-殘讀補完-2026-08-31-三個新參考檔與其餘新節) |
| `v3.1.0` | `f4a95a180404bd4de35365da66849a243e3d07be` | [2026-09-05](#rebelytics-31-改版逐條-2026-09-05-上游在補儀器的守則-我方多半已有) |

血緣旗標對整份文件有效: 上游 3.0 起與我方同名, 本 repo 公開, 誰讀了誰查不到; 每一節的「同形」都只當
佐證, 不算獨立收斂票, 直到血緣查明.

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
## `rebelytics` 3.0 改版逐條 (2026-08-31): 上游朝我方的形狀走了過來

四個來源檔全動 (SKILL.md +403/-325, 其餘三檔共 +1,081), 另新增三個參考檔
(`observation-log.md`, `signals.md`, `migration.md`). 新版位元組:

| 檔案 | 舊 sha256 前 16 | 新 sha256 前 16 |
|---|---|---|
| `SKILL.md` | `60bfdcd99c4678a8` | `a7d1e2074188a7e3` |
| `references/weekly-review.md` | `247e7bfcd4aecc71` | `a00831f044d7e381` |
| `references/skill-authoring.md` | `15fc47365fdfc89c` | `67fee4b5319dfa7e` |
| `references/environments.md` | `0e4274047c6628e8` | `da8a4682abe62b8c` |

**主事件: 儲存模型整個換掉, 換成我方那一類.** 單一 Markdown log 改成**每觀察一檔**
(YAML frontmatter + `NNNN-slug.md`), 封存改成純 `mv`, id 取 max(active, archive,
`.id-floor`)+1. 08-28 逐條處置裡我方寫「上游是要求模型小心維護一份 Markdown; 我方把它
交給工具」「archival 那整類危害在我方設計裡不存在」—— 新版上游自己也到了: 原文寫
"a new file never touches another entry's bytes", 然後把整套 Log-write safety 儀式
(backup→re-read→merge→invariant→survival check) **全部刪掉**, 因為設計讓危害不可能.
危害用位置解不用提醒解 —— 這是該原則第二次被獨立走到.

**血緣旗標, 必須記**: 上游同時把 skill 改名為 `task-observer` —— 與我方改造後的名字
逐字相同 —— 且本 repo 是公開的. 是他們讀了我們, 還是自然命名收斂, **查不到**. 在釐清前,
下表所有「同形」都只當佐證, 不算獨立收斂票 (與 sepia 同一條紀律).

### 新規則逐條 (讀了 SKILL.md 全文 diff 與 skill-authoring 兩節)

| 上游新規則 | 處置 | 依據 |
|---|---|---|
| **空掃描守則**: 已知非空的 log 掃出空結果 = 壞掉的指令, 不是「無相關觀察」; 檔數用字面路徑獨立數, 與解析數比對, 不符就 halt; 路徑在同一個 tool call 內重推導 | **已落地 (佐證+1)** | 與我方 rtk 那條「rewritten command 報 0 matches 不得記為 no hits, 用絕對路徑重跑比對」同一條原則; 這是第三個獨立血緣 (rtk 經驗, rebelytics 舊版 id 規則, 現在的空掃描守則) |
| **延遲的第二張皮**: 「先等幾天真實使用再說」讀起來像嚴謹所以沒人挑戰; 寫下任何「later」前必須指名**哪一個具體觀察會改變決定, 它何時可能到** — 指不出來就是現在動手; 延遲是決定, 要跟行動一樣付理由 | **已落地 (同日對上)** | `pending-evidence.md` 每項強制「觸發事件 + 判定規則」正是這個形狀; 上游把「指不出觸發 = 立刻動」這半句說得更利, 收進該檔導言 |
| **強制觸發必須掛在 tool record 可見的事件上**, 絕不掛在「模型注意到某時刻符合資格」; 綁單一工具的計數器在不用該工具的 session 裡靜默失效, 永遠要第二條獨立路徑; deploy/release/push 這類收尾指令一律當 flush 點 | **佐證 (軸二)** | 我方執行軸 (prose→gate→instrument) 的同一個結論: 自我評估在負載下先壞. 「綁單一工具的計數器會靜默失效」是我方還沒說過的精確化, 值得引用 |
| **`parked` 狀態**: 決定了但被外部前置條件擋住的觀察離開佇列, 強制 `parked_until:` 一行寫明解鎖條件, 不封存也不再被 review 重新抬升 | **佐證** | 與 pending-evidence 的「等一次觀察」欄同構: 等待要有名字與條件, 不然每次 review 都重付分類成本 |
| **siblings_checked 強制欄**: 目標 skill 屬於家族時, 寫觀察前逐 sibling 判斷適不適用並記下裁決 (含「查了, 不傳播」); 快篩: 這句話拿掉工具名還成立嗎 | **佐證 (雙生)** | 我方 TWINS 是同一題的雙生版; 「一筆單目標紀錄在位元組上看不出 sibling 是評估過還是沒想過, 只有記錄欄位讓缺席可見」與我方「沒查和沒動要分開」同一條 |
| **讀全文才准處置**: 解決/駁回/引用前必須讀 body 不是標題; 平行發現疑似重複時 diff 兩個 body — 第二筆常是精煉不是回聲; 表面同意比反對更能壓抑查證 | **已落地 (佐證+1)** | 「狀態要當場觀察」與 QC fraud 清單的同族; 「同意壓抑查證」是好措辭 |
| **staging-only 無互動例外**: 「使用者記得的例外就是遲早被留開的閘門」 | **佐證** | 與我方 push 逐次授權同形 (一次 ok 只算一次) |
| **拒寫≠唯讀**: 寫入被拒先重試一次+換介面, 報「失敗 N 次」絕不報「做不到」— 機率性守門員的連續拒絕是雜訊不是牆 | **不採用 (機制), 佐證 (措辭)** | 我方 harness 的拒絕語意不同 (拒絕=使用者決定, 不重試原句); 但「報失敗次數不報不可能」值得記 |
| **Trial design**: 量「行為會不會自己觸發」時, 觸發條件必須寫在受測 agent 讀不到的通道; 任何 priming 文本點名觸發條件的 session 一律作廢; 負例要主動記錄 ("in scope, no organic load") | **已落地 (佐證+1), 一半是新的** | 前半正是 s7 兄弟 fixture 污染與「計數探針把自己算進母體」的同族 — 我方付過兩次學費; 「null 結果要主動記錄」直接命中 No-ops 待辦, 佐證+1 |
| **Timelessness**: 共用 skill 不得寫無日期的現在式狀態句; sweep "currently/now/as of"; 但**發布物該把作者查核日期換成 verification-based 措辭** | **前半已落地, 後半不採用** | 前半是「只記上游不記本機」+ evidence-check 的 dated-claims 掃描 (30 天陳化表); 後半與本 repo 相反 — 這裡是研究 repo, 逐日期是制度不是洩漏 |
| 首跑 backfill: log 空而專案有歷史時, 掃 CLAUDE.md/commit 史一次性補記 | **不採用** | 背景啟動類, 我方只在摩擦後觸發 — 與 08-28 對 session-start 掃描的裁決同一條線 |
| 三新檔 `observation-log.md` / `signals.md` / `migration.md` 與 weekly-review/environments 其餘節 | **未讀, 排隊** | 見「沒有查的」 |

### 沒有查的 (本輪)

- rebelytics 三個新參考檔與 weekly-review (+354) / environments (+286) 的全文,
  skill-authoring 除兩節外的其餘新節 (三容器規則, versioning, retiring-harvest,
  external tool surface). SKILL.md 是核心已全讀; 其餘排入 pending-evidence.
- Headroom `Unreleased` 段只讀了 changelog 敘述, 沒有讀 PR diff.
- Deep Agents 三個 package 的版本內容差異.
- Pilotfish v1.4 的 plugin 化只讀了兩篇 release note, 沒拆內容 — 排 peer-harness 輪.
- eli5 的 path commit (API 查無, 可能 path 改了) — 下輪先修查法.
- AA Index 版本沒查.

**推翻條件**: 若血緣查明 rebelytics 3.0 參照過本 repo (改名 + 儲存模型兩個同形同時
出現是最強的一筆線索), 上表與 08-28 節的所有「獨立走到」全部改記同血緣, 且第四輪整合
的收斂計票要把 rebelytics 從獨立票中剔除.
## `rebelytics` 3.0 殘讀補完 (2026-08-31): 三個新參考檔與其餘新節

08-31 那輪只讀完 `SKILL.md` 全文 diff, 其餘排隊. 本節補完. 新檔位元組:

| 檔案 | sha256 前 16 | bytes |
|---|---|---|
| `references/observation-log.md` | `c29dc5c13cecfdc3` | 20190 |
| `references/signals.md` | `6f77ff5af42bcd0a` | 3916 |
| `references/migration.md` | `ba788539a5ff3a24` | 6668 |

### 逐條

| 上游規則 | 處置 | 依據 |
|---|---|---|
| **skill 家族與 sibling 漂移**: 一套方法配不同工具/主題時, 共用的那半預設會漂, 因為每個成員只在用到它的 session 裡被維護, 沒有人看整組. 實測「純認識論, 五個成員都適用的規則, 只存在於五分之一」 | **佐證, 而且我方當天實測到同一個比例** | 2026-08-31 落地 untrusted-input 邊界時的讀數正是**五支裡一支有** —— 兩邊獨立量到同一個形狀. 這是本輪最強的一筆佐證 |
| 兩個便宜的傳播測試: (a) 這句話拿掉工具/主題名還成立嗎; (b) **規則自己宣告了普遍性**(「applies to any…」「not specific to X」)—— 那種措辭是最便宜的傳播訊號, 要有機制注意到它 | **採用 (b), (a) 已落地** | (a) 等同我方 TWINS 的判準; (b) 是新的, 而且**可機械化**: 對自己的 skill grep 宣告普遍性的措辭, 再查那條規則在不在 sibling 裡. 進落地評估 |
| `siblings_checked` 強制欄的理由: 「查過而正確排除」與「從未想過」在位元組上一模一樣; 記錄裁決不會讓裁決變好, 它讓裁決的**缺席**變得可見 —— 那是唯一能被強制的性質 | **已落地 (同日)** | `harness-review` 那格「查了, 不補」正是照這條寫的 |
| 「寫規則的人自己在同一個 session 裡違反了那條規則」(四筆 under-scoped) | **佐證** | 與我方「一天之內兩次都是自己的儀器」同類 —— 指令本身不是強制力 |
| **註冊表會過期, grep 不會**: 前三部分只管往後, 機械稽核才抓得到規則之前就存在的漂移 | **採用** | 與我方「量測面指紋 vs 人工清單」同一條; 本 repo 的 twin-guard 待辦正缺這一半 |
| 每觀察一檔讓整套並行儀式消失 (單檔時代曾有一次 greedy 取代覆蓋掉 16 筆, 一次 write-back 抹掉剛追加的兩筆) | **已落地 (形狀不同, 同一結論)** | 08-31 前一節已記 |
| **git 危害**: `git clean -fd` / `checkout --` / `stash` 會清掉觀察檔, 而**剛寫的觀察是未追蹤檔**, `git clean` 存在的目的正是刪那些; 而持續寫入的 log 通常正是讓樹變髒的原因 | **不採用 (位置已解), 但值得記** | 我方帳本在 `~/.agents/telemetry/` 絕對路徑, 在任何 repo 之外, `git clean` 碰不到. 又一次「危害用位置解不用提醒解」 |
| checkpoint 為什麼是寫入不是自問 | **佐證** | 同 08-31 已記的軸二 |
| `signals.md` 的**普遍性測試**四問, 與「知道什麼**不該**學和偵測訊號一樣重要; 從孤例過度學習正是 skill 漂成過度specific的路徑」 | **佐證** | 等同我方「無 failing trap, 無規則」與 L1–L6 那組; 上游把反面說得更清楚 |
| **三容器規則**: 需要個人/團隊特定值的 skill 要三個容器 (skill 存流程並讀設定, 私有 config 存特定值, 呼叫 prompt 只存觸發). 附帶一條: **prompt 或 config 為了保險而複製 skill 規則時, 用停止條件取代那份複本, 不要用比較短的複本** —— 以保險為名的重複是最少被稽核的那種, 因為支持複製的理由同時也是反對質疑複製的理由 | **原則已落地, 後半那句採用** | 我方「同一規則只保留一個真相源」是同一條; 「以保險為名的重複最少被稽核」這個措辭比我方任何一句都利 |
| **retiring skills: harvest before you retire** —— 方法論與包在外面的客戶設定壽命不同, 一起退休等於在成本已沉沒的那一刻丟掉耐久的那一半, 而且**沒有任何東西會報錯** | **不採用 (無對應形狀)** | 本 repo 沒有客戶委託模型; trap suite 退場時形狀類似但尚無實例 |
| **versioning**: 版號是對歷史與相容性的宣稱, 不是 tag 計數器; 破壞既有安裝路徑就是 MAJOR; 次要版本面 (registry/manifest) 要在打 tag 前同一次 push 對齊 | **不採用** | 本 repo 不發版 |
| session-start hook 計算狀態並注入, 因為「review 觸發是軟步驟, 會和 activation 一樣被跳過, 而且失效是自我隱蔽的」 | **佐證, 且對我方待辦有用** | 見下 |
| **commit identity**: 寫入憑證與 author email 是兩條獨立通道; 第一次 commit 前先驗 `git config user.email` 解析到預期帳號; 已發布的 main 不為了修 author metadata 而改寫 | **已落地 (當場驗過)** | 本 repo 是 repo-local config, `Yuhuan <lfm85768@gmail.com>`, 對得上. 「fix forward only」與我方 08-31 那次 history rewrite 的教訓同向 |
| `migration.md` 全文 (pre-3.0 單檔 log 的一次性轉換腳本) | **不採用** | 我方沒有那個舊格式 |

### 那個 session-start hook 對我方待辦說了什麼

[landing-readiness](landing-readiness.md) 的建議三 (SessionStart 注入當量測位置) 被三道關
擋著, 其中最硬的是「沉默會被讀成通過」. 上游給的不是機制, 是**測法**:

> 對 `never`, 30 天前, 2 天前三個 fixture 各跑一次, 確認第三個保持安靜.
> **一個從來不會響的提醒, 和一個正確地安靜的提醒, 在通過的那一次跑裡長得一模一樣.**

那句話是我方「會說謊的 gate 比沒有 gate 糟」最利的一種說法, 而它附帶的處置是**用 fixture
把每一個分支都證一次, 包含必須安靜的那個分支**. 我方 mutation 測試已經是這個形狀, 所以
這是佐證不是新機制 —— 但它把建議三的第三道關從「無解」變成「有已知做法」: 要量注入位置,
得先有一個能證明警報會響的 fixture. 這不解決前兩關 (reach marker 與構造不轉移).

### 沒有查的

- `weekly-review.md` 的其餘新節只讀了 Family coherence 與 Parked 兩個標題層的模板行,
  沒有讀完整步驟.
- `skill-authoring.md` 的「Documenting an external tool surface」整節沒讀.
- `environments.md` 的 Environment mappings, Storage regimes, Git as staging medium,
  First-run backfill 四節沒讀.
- **血緣仍未查** —— 改名與儲存模型兩個同形的成因不明, 上表所有「佐證」仍受 08-31 那條
  推翻條件約束.

**pin 仍不推進**: 逐條已補齊, 但 `task-observer` 是從舊版蒸餾的, 而新版是重寫等級的改動;
推進 pin 等於宣稱我方已對齊 3.0, 那要一次完整的落地評估, 不是一次閱讀.
## `rebelytics` 3.1 改版逐條 (2026-09-05): 上游在補儀器的守則, 我方多半已有

`v3.0.0` (`9d1491b8`) → `v3.1.0` (tag `f4a95a180404bd4de35365da66849a243e3d07be`, 2026-09-04).
+43 commit, 五天內 (08-31 到 09-04), 其中 27 個是 09-04 一天合的; README 自述 82 個 issue,
23 個 PR, 44 位貢獻者 —— 這個上游的 issue 流量是它負結果的來源, 權重要算進去. 七個來源檔動六個,
另新增一個. 位元組 (tag 與 head `2967fa5f` 八檔全同):

| 檔案 | 舊 sha256 前 16 (v3.0.0) | 新 sha256 前 16 (v3.1.0) | 行數 |
|---|---|---|---|
| `SKILL.md` | `a7d1e2074188a7e3` | `d5604bb4385ba855` | 524 → 709 |
| `references/environments.md` | `da8a4682abe62b8c` | `c9c46ca1ccded8f7` | 371 → 485 |
| `references/migration.md` | `ba788539a5ff3a24` | `bec6e12d29005b9c` | 143 → 189 |
| `references/observation-log.md` | `c29dc5c13cecfdc3` | `b26b7ab1ad682af7` | 348 → 469 |
| `references/skill-authoring.md` | `67fee4b5319dfa7e` | `27f28a110b75b668` | 660 → 712 |
| `references/weekly-review.md` | `a00831f044d7e381` | `b15aaebf36d1bea8` | 507 → 668 |
| `references/signals.md` | `6f77ff5af42bcd0a` | 未動 | 81 |
| `references/starter-principles.md` | — | `236c531953199b8a` | 新, 296 |

**主事件: 這一版幾乎全是儀器守則, 不是流程.** 3.0 換了儲存模型; 3.1 在儲存模型上補的是
「指令為什麼會靜默失效」的守則: 絕對路徑, 探針要當回合跑, 空結果是儀器的問題, 觸發要用真實
tool record 做正負控制, 指標要耐久. 這條線我方走在前面 (rtk 那條, `AGENT_SKIP_TEST_GATE`
那條, 戳章分組那條), 所以下表大半是已落地加佐證; 真正沒有的是四條, 全部排進
[升級計畫](../plans/upgrade-plan-2026-09.md). 血緣旗標維持: 上游 3.0 起與我方同名, 同形一律
只當佐證, 不算獨立收斂票.

### 新規則逐條 (讀了 SKILL.md 與五個 reference 的全 diff)

| 上游新規則 | 處置 | 依據 (查了什麼) |
|---|---|---|
| **穩定 ≠ 單一**: Claude Code 的專案身分來自開 session 的目錄, 在子資料夾開 session 會把 log 切成幾個各自「穩定」的碎片; 全域安裝的 skill 要釘一個 user-scope 路徑 | **已落地 (設計上)** | 我方 ledger 是單一 user-scope 檔 `~/.agents/telemetry/skill-observations.jsonl`, `ledger_path()` 只看 env 與 HOME, 不看 cwd |
| **每個可執行片段帶釘死的絕對路徑** `[ABSOLUTE PATH]`; 從別的目錄用相對路徑跑不會錯, 會報「空的乾淨 backlog」—— 唯一沒人質疑的答案 | **已落地** | 同上; `observation-log` 是腳本不是片段, 路徑在腳本內解析 |
| **啟動種子** `starter-principles.md`: 首跑時二選一 (空 / 種), 種進去的每條帶 `Origin: imported from starter set`, 絕不靜默預填 | **不採用** | 我方沒有 principles 檔; `review.md` 明文「不維護第二份可變 principles 檔, event ledger 是證據源」. 25 條種子本身另表逐條 |
| **掛載探針要在同一回合跑**; 不得從環境旗標, context 裡有沒有設定檔, 或上一回合的記憶斷言掛載狀態; 探針失敗先叫 folder-picker, 不是走「沒有檔案系統」分支 | **佐證** | 「狀態要當場觀察」與 QC fraud 清單同族; Cowork 的 picker 機制不適用 |
| **session-start 掃描不能替代 per-skill 查詢**: 範圍, 深度, 時刻三者都不同; 一百個標題的知覺撐不過二十個 tool call; 檢索要發生在決策的位置 | **佐證 (Context 層), 且是一個跨上游的分歧** | 與 wording-effect-scale「淺層介入撼動不了深層結構」同向; 但 Pilotfish 1.4 把政策搬**進** SessionStart 注入 —— 兩個上游對「注入在 session 開頭有沒有用」站相反邊, 記進第四輪整合素材, 我方的注入位置實驗 (pending-evidence 三之七) 正是能裁決它的量測 |
| 掃描片段改寫: `find` 不用 glob (zsh `nomatch` 會讓空 log 直接 abort), 計數用獨立指令不用迴圈內的計數器 (pipe 後的 subshell 會讓它歸零), 守衛用 `if` 不用 `&&` 鏈 (健康掃描以 exit 1 收尾) | **不適用 (我方是 Python), 佐證 (三條性質)** | 「守衛要在它守的那條 stream 之外」是好措辭; 我方 diagnostic hook fail-open / gate fail-closed 的分工是同一題的另一面 |
| **staged-work 三向對帳**: 安裝在 session 之外發生, 沒有 session 看得到, 所以清理綁在「讀到 manifest」那一刻; `diff -rq` 分三種 (相同→已裝, live 嚴格較新→superseded, staged 有 live 沒有→未裝) | **已落地 (形狀不同)** | `sync.sh --apply` 之後跑 rsync parity 加退役檢查; 我方 live 副本從不合法地自己往前走, 所以沒有 superseded 這一類. dry-run 不是 parity check 這件事 (記憶裡有) 維持不變 |
| **未解的缺陷是一則觀察, 在一個有界的點上**: 缺陷不是交付物又吃掉 session 時, 停止點要在第二個假說前設, 「症狀 + 排除了什麼 + 最便宜的下一步」的報告本身是交付物; 這個 skill 不帶除錯方法, 只帶邊界上的捕捉規則 | **改造後採用 → 計畫 P5** | `evidence-debugging` 只有 diagnose/repair 的權限切分與「無迴路即停」的閘, 沒有「除錯不是任務時的預算」; 是 prompt surface, 要位移與重跑 census, 所以排計畫不當場動 |
| **flush 是性質不是清單**: 任何「向人宣告一個工作單位完成」的動作都算 (完成通知, 最終報告, 狀態檔寫 done); 清單繼承它被推導出來的那些 session 的形狀, 在用別的工具宣告完成的 session 裡靜默失效 | **不採用 (機制), 佐證 (措辭)** | 我方寫入 opt-in, 整個 flush 類不存在; 「清單繼承推導它的 session 的形狀」與我方「綁單一工具的計數器靜默失效」是同一條, 這句更利 |
| **可見是必要不是充分**: 觸發的 pattern 是對未來 tool record 的宣稱; 上膛前要用專案**真的**產生的事件字串當正控制, 真實 tool record 裡一個非事件當負控制, 絕不用造的例子 (它取樣的是作者的模型, 也就是漏洞的來源); 兩個結果記在觸發旁邊. 觀察到: 六個 pattern 從 deploy 腳本內部推出來, 從沒 match 過專案真正打的指令, 同日卻在一個含訊號字的唯讀指令上誤發 | **已落地一半, 佐證+1; 執行面 → 計畫 P6** | 我方測試有負控制 (test_mechanisms `test_it_ignores_tools_that_do_not_write` 那類); commit-test-gate (Bash hook 那一道) 的 `SKIP_RE` 是對真指令調的, 而 git pre-commit 那一道守的是文字到不了的路徑, 兩道各自要有自己的正控制; 「絕不用造的例子」與「兩個結果記在觸發旁」是精確化. `CARRIER_VALIDATED_ON` 就是這條的本地形狀, 而 weekly-integrity 今天報它在 2.1.261 未驗 —— P6 用一次真派工做正控制 |
| **不得替後面那層預先做交付決定** (「收件人就在旁邊, 不用送」): 先發, 讓擁有那層的機制壓下去 —— 被壓的送出在 tool record 留痕, 沒送的什麼都不留 | **佐證** | 我方固定 `[LEAF_DISPATCH]` / `[LEAF_RESULT]` 紀錄每次都出, QC 壓不壓另計; 同一原則 |
| **封存騎在 id 推導指令裡**, 不是寫前的前置義務: 「附在另一個動作前面的義務不繼承那個動作的強制力; 一定要伴隨 tool call 的步驟, 放進同一條指令, 不放在旁邊的散文裡」 | **已落地 (設計上), 佐證+1** | 我方 UUID + append + exclusive lock, 沒有 id 也沒有封存; 那句話是執行軸 (prose→gate→instrument) 最短的表述, 值得引 |
| `noclobber` 建檔, 同 id 同 slug 才會覆寫, 碰撞就重推 id; `sed` 去零填充 (shell 算術把 `0105` 讀成八進位) | **不適用** | UUID |
| **寫前立刻跑 id 片段, 包括 session 唯一一次寫**; 先前為了別的目的讀過 log 不算 —— 「篩選」與「最大值」是同一份資料上的兩個問題, 一個的答案不是另一個的證據; 相關性 grep 回的是最高的**相符**項不是最高項, 而且不讀 archive 與 `.id-floor` | **已落地 (設計上), 佐證+1** | 與 upstream-distillation 的「reconcile counts; never build the work queue on a filter」同一條, 上游把「篩選 ≠ 最大值」說得更利 |
| **每個儀器同一條守則, 當性質不當清單**: 空或零的結果先是對儀器的宣稱, 直到獨立探針證明母體真的空; `SCAN COMMAND BROKEN` 與 `ID COMMAND BROKEN` 是一條規則的兩個實例; 逐片段列舉的守衛對下一個片段沒有防護 | **已落地, 佐證+1 (第四個血緣)** | rtk 那條 (絕對路徑重跑), evidence-ladder 的儀器校準, upstream-distillation 的「先對已知存在的東西跑一次探針」, 加上這條; 「當性質不當清單」是我方沒說過的話 |
| **`parked_until` 要發生得了**: 問誰或什麼得動它, 那一方有沒有理由做恰好相反的事; 發生不了的條件與靜默丟棄無異, 只是更貴, 而且比模糊的條件更像嚴謹 | **採用, 已落地 (本輪)** | 收進 [pending-evidence](../plans/pending-evidence.md) 導言那條入場檢查的第二句 |
| **`reference:` 要是耐久可解析的路徑**: 活過 session 與重開機, 別的 session 解析得了; session 暫存目錄兩者皆敗, 「那個 scratchpad」「我的筆記」不是路徑; 這種指標寫時不會失敗, 讀時才失敗, 而作者已經不在 | **採用 → 計畫 P2 (兩個獨立血緣); 2026-09-05 量過不加: 2 命中 0 缺陷, 數字在計畫 P2 列** | 本 repo 09-04 為了同一件事下過 commit `c995eb6` (把五十個 run 在 scratchpad 消失前保留下來); 兩邊各自付過. 我方沒有掃描: `docs/` 與 `main/.agents/docs/` 對 `/private/tmp`, `/tmp/`, `scratchpad` 今日 2 命中 (`clause-pricing.md`, `context-and-vendors.md` 各一, 真偽未分類 —— 那是 P2 的第一步), 規則要不要加看三個數 |
| **carrier pattern**: `status:` 是每則一個而 `skill:` 是清單, 生命週期欄比它追蹤的工作粗; 部分處理時把紀錄沿工作的縫拆開 —— 原則: 當一個紀錄的生命週期欄粗於它追蹤的工作, 每次狀態轉換都對某個讀者說謊 | **不採用 (形狀沒有), 佐證 (原則)** | 我方 `--skill` 一個名或 `all-skills`, resolve 逐則; 部分處理本來就是另開一則 |
| **對帳斷言是時點斷言不是持續保證**; 多寫者 log 在長 review 中衰減; 留 Step 1 清單, Step 6 重掃, 「Arrived during this run」那行絕不省略 | **佐證** | 「絕不省略的 none 行」就是 08-31 收的 No-ops 規則; 多寫者衰減對鎖住的 JSONL 加唯讀 review 不適用 |
| **前提先查再給選項**: 檔案層出處 (是不是外人維護) 與節層出處 (這節是不是本地加的) 是兩句話, 都從本地副本答得出; 遠端的那一半 (上游 HEAD 還有沒有這節) 不得讓 review 依賴網路, 標成 unverified 交給 pre-flight. 觀察到: 三則觀察被派去「貢獻上游」, 那一節其實只在本地 fork 裡 | **已落地, 佐證+1** | 這就是 ATTRIBUTION 的 substantial portion / concept rewrite / added locally 三分法, 與 pin-report「連不上 ≠ 沒動」; 上游把「兩層各答」說得比我方清楚 |
| 排程器偵測按平台 (Windows 是 Task Scheduler; 只查 cron 會把每台 Windows 標成沒排程器) | **不適用** | 只部署 macOS; weekly-integrity 掛 SessionStart 不掛排程器 |
| `{skill}-extras` 伴隨 skill 是 review 裡「不開新 skill」的唯一例外 | **不適用** | 沒有伴隨 skill 路由; 我方對 local-or-third-party 是停下來 |
| **回饋 pre-flight 在 apply 時跑** (重複搜尋, 維護者偏好的管道, 上游 HEAD 驗證); 空的重複搜尋要先過正控制才放行 | **已落地** | 探針校準那條; 我方不對上游發 PR, pre-flight 本身不適用 |
| 先選 anchor: 同日第二輪用 `<date>.2` 這種區分過的 anchor; 守衛拒絕在既有 anchor 上重種 | **不適用** | 沒有 staging 目錄, sync 直接替換 |
| **交付前閘第 6, 7 條**: 恰好一個 frontmatter 區塊; 編輯殘渣 (`\1` 孤行或散文裡的字面 backreference, conflict marker, `{{slot}}`, `TODO: fill`) 當唯一的內容斷言, 掃整個 bundle 的文字檔, 程式碼圍欄先遮掉但行號保留 —— 因為一個字面 `\1` 曾經穿過 apply, gate 與 install | **採用 → 計畫 P3; 2026-09-05 已落地 (`test_deployment.EditResidueTests`, 0 命中先量過)** | 我方 `main/` 的 md/toml/json/yaml 今日 0 命中 (P3 三個數之一); test_contracts 有 frontmatter 解析, 沒有「恰好一個區塊」的斷言 |
| **keep-two 數的是輪不是天**; 刪目錄前先列裡面還有什麼 (組裝腳本, 驗證腳本, 工作筆記), 先搬開再刪 | **佐證** | `evals/scripts/retain.py` 數的是 run; 「刪前先列」是好習慣, 我方沒有等價的自動刪除 |
| **manifest 不帶後續工作**: review 認出的「下次查」在寫摘要前先變成自己的觀察 (開了就 parked); 壽命止於安裝的產物載不了後續 | **已落地** | pending-evidence 是唯一佇列; link, don't repeat |
| 四級啟用: 新的第二級是 **user-level preferences** (與資料夾無關, 每個 session 都注入), 是「先探針再請求」那一行的正確歸宿, 因為工作區內的設定檔在沒掛載時恰好不在 | **已落地** | 全域 `~/.claude/CLAUDE.md` 就是這一級, 我方契約住在那裡 |
| **每次載入 skill 都對 log 做 body 層 grep**; session-start 掃描不涵蓋它 | **不採用** | 08-28 對 session-start 掃描的裁決同一條線: 我方只在摩擦後觸發, 不做載入時掃描; 分歧記入整合 |
| **釘根, 列衍生路徑**: 只釘 observation-log 目錄讓 staging 根, manifest, principles 檔各 session 重推, 三個寫者出現兩個 staging 根 | **已落地 (設計上)** | 單一 ledger 路徑, 沒有 staging 根 |
| hook 數 `status: open` 不數檔案 (今天解決的檔還留一天); 日期比較不用 `\<` (zsh 拒絕) | **不適用, 佐證 (數對母體)** | 我方 hook 是 Python; 「數的是哪個母體」與戳章分組那條同族 |
| **在新 session 驗證啟用**: 安裝的 session 證明不了 (設定檔在 session 開始讀; 熱載入的 skill 被手動叫過不算); 報「activation unverified」直到新 session 自己叫了它; 外部診斷: 幾個 session 後 `observation-log/` 不存在就是從沒啟用 | **已落地, 佐證+1** | `CARRIER_VALIDATED_ON` 戳章 + weekly-integrity 的「unvalidated on this runtime」就是這條; 今天它正好開口. 執行 → 計畫 P6 |
| **hook 安裝被擋走同一套退路**: 不換工具重試, 不繞, 先報拒絕, 最輕的先 (請求重試 / 給使用者 JSON 自己加 / 臨時授權 / 退到宣告式指令並明說強制級不在); 靜默失敗的 hook 安裝比沒有更糟 | **已落地** | `sync.sh` 用 `merge-settings.py --check` 的冪等驗證, hook 沒合進去會讓 sync 大聲失敗 |
| **受管的 skills 目錄** (chezmoi, stow, symlink 到 dotfiles): live 路徑不是真相, 複製上去看起來裝了, 下次 `apply` 靜默還原; 安裝時偵測管理器, 寫進管理器的 SOURCE; 讀仍讀 live | **已落地 (從另一方向), 佐證+1** | 我方「Git checkout 是權威, 絕不編輯 `~/.claude/skills` 副本, 部署會替換」+ `.agent-harness-source` 標記; 兩邊各從自己那一端走到「寫要寫源頭」 |
| **sibling-sync 註記要尊重發布邊界**: 公開 skill 裡的家族引用用能力語言, 不點名已裝未發布的 skill —— 維護機制寫進產物的交叉引用, 得尊重那個產物的發布邊界 | **已落地, 佐證** | 部署檔「用名字不用連結」「不帶 bare short SHA」(docs/README 規則 9): 指標要在讀者的世界裡解析得了 |
| **建議的檢查帶三個量測數**: 對既有語料先跑, 記今日命中 / 其中真缺陷 / 去掉其餘所需的正規化; 一個未量假陽性率的規則是一個「讓人忽略測試」的提案 | **採用, 已落地 (本輪)** | 收進 `.claude/skills/upstream-distillation/SKILL.md` 守衛那條; 計畫 P2, P3 照它走, 三個數各先量 |
| 驗證前先正規化行尾 (CRLF 讓 `diff -rq` 每個文字檔都變, 兩張 PNG 相同就是線索) | **不適用** | macOS/LF; 記在搬遷檢查旁作為外部注意事項 |
| **替某個專案寫 skill 前, 先查它自己有沒有帶** (`agent-skill/`, `.claude/skills/`, README); 有就裝官方的, 本地差異放伴隨 skill | **前半已落地, 後半不採用** | 前半就是 upstream-distillation 的勘查; 後半與記憶裡「蒸餾不安裝 plugin」相反 —— 安裝會註冊整個 marketplace, 我方要的是規則不是套件 |
| 搬遷: 先列舉這台機器其他工作區 (`find ~/.claude/projects -name log.md`); 幾個 legacy log 觀察同一批全域 skill 不是幾個 scope, 是分叉; 完成註記寫進全域文件時要點名涵蓋哪些工作區 | **不適用, 佐證 (最後一句)** | 沒有 legacy log; 「全域文件裡的 done 讀成到處都 done」與通貨表 Headroom 列的「只記上游不記本機」同一條 |
| `migrate-log.py`: skill 名可以是 `plugin:skill` (冒號是名字的一部分, 是 Skill 工具實際吃的字串) | **採用 (縮小) → 計畫 P1** | 我方 `observation-log target` 的 `SKILL_NAME` 是 `^[a-z0-9]+(?:-[a-z0-9]+)*$`, 對 `codex:rescue` 這種本機真有的 plugin skill 直接 `LedgerError`; `add` 走 `require_text` 不擋. 先寫紅測試再放寬 |
| `migrate-log.py`: 一個壞 token 不要旗標兩次; stdout `errors="replace"` (cp1252 主控台在寫完檔後才炸) | **不適用** | 沒有 migrate; UTF-8 主控台 |
| `validate-skill-bundle.py`: 第二個 frontmatter 區塊, 殘渣正規式清單, 遮圍欄保行號 | **併入 P3** | 實作細節可借 |
| README 「Check that it actually runs」+ 外部診斷 | **已落地** | 同上 activation 那條 |
| CONTRIBUTING: 發版前逐 commit 查 `Co-authored-by` / `Reported-by` trailer | **不適用** | 單人 repo |

### `starter-principles.md` 25 條種子逐條

上游自己說這是「去掉出處的通用方法論原則」, 所以每條都當規則讀, 不當種子讀. 對到我方的多半是
契約與 skill 裡已有的東西; 沒有的三條都是形狀不同 (互動小工具, 瀏覽器成本, API 沙盒).

| # | 種子 | 處置 | 依據 |
|---|---|---|---|
| 1, 2 | 開源 skill 要有授權, 作者歸屬與回饋管道 | **已落地** | 每個蒸餾 skill 的 ATTRIBUTION 與 LICENSE |
| 3 | 有規則的 skill 要有交付前的自我核對步驟; 「不強制的規則是建議」 | **已落地, 佐證** | commit-test-gate, prompt census, evidence-check 是機器做的核對, 不是模型再讀一遍 |
| 4 | 不含客戶識別資訊, 在寫作/記錄/發布三個時點都擋 | **已落地** | task-observer 邊界; 通貨表「只記上游不記本機」 |
| 5 | 工具中立語言, 但**具體工具名先給再給通用退路** (agent 對工具名做 pattern match) | **已落地, 佐證** | 雙生規則各用自己那側的慣用語就是這條; 「具體先, 通用後」的順序是精確化 |
| 6 | 產結構化輸出的 skill 要用多個真實範例 grounding | **不採用 (沒有這類 skill), 佐證** | trap fixture 與 replay run 是我方的多範例 |
| 7 | 子代理要有完整輸入與經驗證的輸出: 缺值寫 `[VERIFY: …]` 不編; 圖表資料先排好序再交; **判斷類輸出沒有單位可對, 要在能證偽的粒度抽查**; 每個宣稱附可定位證據; 「錯的數字在被拿去算時會炸, 錯的定性被同意就被消化了, 而同意不留痕」 | **已落地, 佐證+1** | baton-dispatch 的 QC fraud 清單, explore agent 回 `file:line`, verifier 觸發; 最後那句是我方 QC 清單的理由, 上游說得比我方好 |
| 8, 9 | 互動小工具失敗的優雅回退; 互動形式配對話能量 | **不適用** | CLI |
| 10 | 小的可行動集合: 內嵌顯示**且**存檔 | **不採用 (作規則), 佐證** | 「產出的檔用絕對路徑點名」是我方那一半 |
| 11 | 修剪與增長同樣刻意: 單一觀察來的規則, 從沒被查的節, 使用者總是跳過的流程 | **已落地** | 預算與位移 |
| 12 | 用來源系統的正典識別碼, 絕不從衍生欄位重建 (從名字造 URL, 從 slug 推 id) | **已落地, 佐證+1** | pin 是 commit 不是 tag; 全 SHA; 「fork 有自己的版本線」 |
| 13 | 讀寫工作區檔案的 skill 要維護一份活的參考檔索引 | **已落地** | docs/README 文件責任表 + `test_document_inventory` |
| 14, 15 | 排程任務叫 skill 不重做 skill; 任務 prompt 是輕量編排, 智慧在 skill | **已落地 (形狀)** | weekly-integrity 叫腳本, 不內嵌邏輯 |
| 16 | 中斷的操作是部分操作: 先驗證狀態再重試, 絕不假設乾淨起點 | **已落地, 佐證** | replay batch 那條記憶 (清 sentinel 前先 `ps`); sync 冪等 |
| 17 | 絕不建議使用者手打技術內容當 workaround | **不適用, 佐證** | 我方要使用者跑指令時給 `!` 前綴, 同一精神 |
| 18 | 瀏覽器自動化是昂貴的最後手段: 記成本, 先 fetch/search, 超過幾次就設檢查點, 不可用時等使用者而不是繞 | **不採用 (作規則)** | 契約已「偏好專用檔案/搜尋工具」; 沒有量過瀏覽器 payload 成本, 不加沒量的規則 |
| 19 | 建議直連 API 時註明沙盒/proxy 的 allowlist | **不適用** | |
| 20 | skill 只留會改行為的內容; 測試是「拿掉這一行, agent 行為變不變」; 範例與反例不砍 | **已落地** | 預算的理由; 這句測試的中文版是 playbook 擁有的原則之一 |
| 21 | 開源 skill 用「the agent」不用廠商模型名, 除非真的廠商專屬 | **部分不採用** | 我方雙生檔刻意各寫各的 provider; 共用的 `.agents` 檔已是中立語 |
| 22 | 查廠商現行指引要看**有日期的 changelog**, 不只文件頁 (快取頁曾落後一週); 「這個屬性不存在」的宣稱需要第二管道 | **已落地, 佐證+1** | 通貨表把供應商指引與供應商製品分類, 製品附觀察日與版本; pin-report「連不上 ≠ 沒動」 |
| 23 | **絕不跨結構不同的分段聚合**; 異質聚合總是抬一段埋一段, **被埋的通常就是發現** | **已落地, 佐證+1** | wording-effect-scale 的戳章分組 (b13ac21: 戳章過期時說得出哪一半動了); 「被埋的就是發現」是新措辭 |
| 24 | **先取得實例再描述它**: 表面 pattern 是關於產物的證據, 因為已在手上而被拿來代替產物; 從熟悉 pattern 來的推論讀起來與驗過的事實一模一樣; 資料集已有分類欄就讀它 | **已落地, 佐證+1** | evidence-ladder; upstream-distillation「讀來源不讀筆記」; 本輪 eli5 又先查錯 path 一次, 正是這條 |
| 25 | **一個查過的理由勝過兩個, 若第二個沒查**: 找第二個理由是在找「指向同一邊的可信東西」; 支持理由拿到的審查最少, 卻是讀者最沒法獨立查的部分; 用文件裡的數字前先確定誰算的 | **已落地, 佐證+1** | evidence-ladder 的循環證明與「方法可借數字不可借」; 契約的「不疊兩層 hedge」是它的反面 |

### 沒有查的 (本節)

- rebelytics 血緣: 仍未查. 3.1 新增的「絕對路徑」「探針當回合跑」「三個量測數」與本 repo 07 到 08
  月的紀錄同形, 線索只增不減; 08-31 的推翻條件維持.
- `signals.md` 未動, 未重讀.
- weekly-review.md 第二段 diff (Step 6 重掃到 manifest 那段) 是從壓縮過的輸出讀的, 已用
  `headroom_retrieve` 對回原文的只有前段; 後段的規則 (Arrived during this run, keep-two 數輪,
  manifest 不帶後續) 分類依據的是原文 diff 檔, 不是壓縮版 —— 記在這裡是因為讀的順序不同.

**推翻條件**: 同 08-31 —— 血緣查明參照過本 repo, 上表所有「佐證+1」從獨立票中剔除. 另一條:
若 P2 或 P3 量出的三個數顯示命中全是正當引用而語料本來就沒有這類缺陷, 那兩條守衛就以
「性質」的形式加 (rebelytics 的措辭) 或不加, 不以「清單」的形式加.
