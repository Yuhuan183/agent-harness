# 機制側盤點: 這 115 個機制各自站在什麼證據上

[← 回研究摘要入口](README.md)

**為什麼有這一份.** 2026-09-08 使用者問「有沒有針對所有研究報告與知識庫綜合下來的評估計劃書,
而且要對應自身專案內容」. 前半已經有三份在答 (下一節), 後半沒有 —— 現有的三份**全部從證據那一側
出發**, 問「語料合起來說該做什麼」. 沒有一份從**機制那一側**出發, 逐個問「這東西憑什麼在這裡,
什麼會推翻它, 誰在盯它不過期」. 這一份補那個方向.

它和另外三份的分工:

| 文件 | 從哪一側出發 | 問什麼 | 現況 |
|---|---|---|---|
| [cross-upstream-synthesis](cross-upstream-synthesis.md) | 外部 | 六個上游**合起來**說明什麼 | 四輪, 結論 1–8 各對到一層; ECC 未進 (第五輪未開) |
| [landing-readiness](landing-readiness.md) | 本目錄 | 我們自己的語料**合起來**說該落地什麼 | 2026-08-31, 覆蓋 18 份, 四項建議全結案 |
| [architecture 第六節](../architecture/architecture.md#六-升級評估-五個問題) | 規則 | 一個改動要過幾關才算數 | 現行, 五個問題 + 每類改動的最低證據 |
| **本文** | **機制** | **每個機制的依據, 推翻條件, 盯的人** | 第一次 |

## 先講覆蓋率, 因為結論的效力受它限制

**這一輪讀了什麼**: 全部 115 個機制的**存在與分類**是機械列舉的 (指令留在下一節);
`docs/hook-system.md`, `docs/architecture/architecture.md` 骨架, `docs/research/README.md` 全文,
`landing-readiness` 前 40 行與骨架, `cross-upstream-synthesis` 骨架與第四輪全文,
`pending-evidence` 骨架, 兩份升級計畫全文.

**這一輪沒有讀的 (2026-09-08 稍晚已補一半)**: 初稿時 21 份研究文裡有 13 份只讀骨架.
同日補讀了六份的結論段 —— `lifecycle-replay` 的「還不能做的事」與注入位置三節,
`clause-pricing` 的 `v1`–`v3`/`m4`, `wording-effect-scale` 的最終帳,
`resident-context-options` 的六分之一節與建議節, `trap-experiments` 的全部輪次一覽,
`cross-upstream-synthesis` 第四輪. 補讀的結果寫在[補讀之後的三條重新結論](#補讀之後的三條重新結論),
其中一條**改變了 M1 的定位**. 仍未讀的是 `landing-log` 系列 (4.6 萬字) 與四份上游分題文件的細部.
本文對「依據夠不夠強」的判斷, 對已補讀的六份是複核過的, 對其餘仍是繼承自述.

**最大盲區**: 依據可能只存在於 `landing-log` 系列 (append-only 原始紀錄, 4.6 萬字) 而沒有被
任何主題文件接手. 這和 `landing-readiness` 的盲區是同一個, 兩輪都沒有解.

## 盤點方法, 以及它第一次就騙了我

列舉是機械的:

```
hook        ls main/claude/hooks/*.py                       11
git hook    main/claude/githooks/pre-commit                  1
skill       main/{claude,codex,.agents}/skills/*/ 去重       10   (+2 repo-root dev-only)
script      ls scripts/*.{py,sh}                            21
script      main/{claude,codex,.agents}/scripts/ 去重        11   (部署到 HOME)
role        ls main/claude/agents/*.md (雙生算一組)            7
eval        evals/replay/scenarios/ 47 + evals/traps/ 5      52
                                                           ----
                                                            115
```

**第一版的探針報錯了.** 我先用「docs 裡提到幾次這個機制的名字」當依據強度, 結果
`codename-gloss-report` 命中 0, 讀起來像一支沒有人要的腳本. 打開它才發現它的 docstring 第三行
就寫著 `docs/README.md` 規則 8 —— **依據記在程式碼裡, 方向和我的探針相反**. 一次改掃全檔加上
反向 (script → doc), 那 0 變成 1.

這值得留著, 因為它就是本 repo 反覆記的那個形狀: 探針的沉默讀起來和「真的沒有」一模一樣.
下面每一個「0」都經過反向複查, 但**只複查了 script 與 hook 兩類**, skill 與 role 那兩類沒有反向掃.

## 主表: 六類機制各自站在什麼上

| 類別 | 數 | 依據落在哪 | 誰在盯它不過期 | 缺口 |
|---|---|---|---|---|
| hook (11) + git hook (1) | 12, **其中 7 個是 fail-closed gate** | `docs/hook-system.md` (10/12 的主要出處, 也是 7 對 5 這個切分的擁有者), 少數在 `landing-log` | 單元測試 + 合成 pipe-test (三關驗證); `denials.jsonl` 記攔截 | **沒有任何一個 eval 情境是關於 hook 的** —— 見缺口一 |

**git 側那一支蓋不到的殘餘**: `--no-verify` 與 `-c core.hooksPath=` 都繞得過去, 所以它涵蓋的是「文字推測不到的路徑」而不是「所有路徑」; 關得起來的那一層是 CI.
| skill (10 部署 + 2 dev-only) | 12 | 各自的 `ATTRIBUTION.md` (去重後 5/12 支有) 或研究分題文件; `baton-dispatch` 21 份文件提及, `test-first-change` 只有 4 份 | `test_contracts` / `test_ledger` 的片語斷言; `prompt-surface-census` 盯位元組 | 出處覆蓋率 5/12, 排 [ECC 計畫 Q10](../plans/upgrade-plan-ecc-2026-09.md) |
| repo script (21) | 21 | 10 支在檔內引用了它服務的文件; 11 支沒有 | 21/21 被套件引用; 抽查確認多數被 `load_module` 或 subprocess 跑過, 但**至少 `docs-size-report.py` 只出現在一行註解裡** | 「跑得動」不等於「有人讀」—— 見缺口二 |
| 部署 script (11) | 11 | `dispatch-lifecycle.md`, `provider-routing`, `experience-ledger` 的 references | `weekly-integrity` 每週自動讀其中 3 支 (`delegation-report`, `prompt-bundle-report`, `experience-report`) + `model-routing` | 另外 7 支沒有排程讀者 |
| role (7 × 2 provider) | 7 | `dispatch-lifecycle.md`, `architecture.md`; `verifier` 25 份文件提及, `security-reviewer` 6 份 | `test_roles.py` 斷言 no-write role 沒有任何 Bash 表面 | 依據厚, 這一格沒有缺口 |
| eval (47 replay + 5 trap) | 52 | `lifecycle-replay.md`, `trap-experiments.md`, `clause-pricing.md`, `wording-effect-scale.md` | `surface.tsv` 戳章; `scenario-index.py` | 全部瞄準契約與 skill 行為, 沒有一個瞄準 gate |

## 三個缺口, 都是量到的

### 缺口一: 證據厚的地方和機制厚的地方幾乎不重疊

`evals/` 底下 52 個情境, 累計 463+ 個 replay run, 沒有一個是**關於某個 gate 會不會擋**的.
全 repo grep 七個 gate 名字, `evals/` 只命中三處, 而且都不是情境: `lifecycle-criteria.py` (判準),
`surface.tsv` (量測面指紋), 和一個 run 的 `replies.md` (偶然提及).

五個 trap 量的是 false completion, spec conflict, tz bucketing, skill recall, pointer redundancy ——
全部是契約與 skill 的行為. 47 個 replay 情境量的是派工成本, 措辭效應, 語言子句, 注入位置.

**數字要精確**: 真的攔得住東西的是 **7 個 fail-closed gate** (`commit-test-gate`, `push-consent-gate`, `leaf-redispatch`, `runtime-guard --gate`, `verifier-quota`, `managed-target-guard`, `githooks/pre-commit`), 另外 5 支是 fail-open 只記錄. **12 是 hook 數不是 gate 數**, 而下面 M1 與 M5 的對象是那 7 個 —— fail-open 的 5 支沒有命中數也沒有停止條件可寫.

**所以我們的知識庫是關於「模型會不會照契約做」的, 而我們的機制有一半是「模型做了會不會被擋住」.**
後者目前只由單元測試與合成 pipe-test 支撐 —— 那證明的是**程式邏輯對**, 不是**放在真實 session
裡有用**. `hook-system.md` 的三關驗證誠實地只宣稱前者.

這不是說 gate 沒有價值: `denials.jsonl` 有 28 筆真實攔截, 那是「它真的擋過」的直接證據.
缺的是「擋了之後結果比較好」, 而那正是[研究摘要驗證缺口](README.md#驗證缺口)第五條
(「從來沒有量過規則觸發了有沒有比較好」) 在契約層講的同一件事, 只是沒有人在 gate 層講過.

**這一格是本次盤點最值錢的發現**, 而且它剛好和 [ECC 計畫 Q3](../plans/upgrade-plan-ecc-2026-09.md)
撞在一起 —— fact-forcing 的第一階段 (只記錄不攔) 產生的就是 gate 層的第一批行為資料.

### 缺口二: 儀器跑得動, 但多數沒有排程讀者

**2026-09-08 分檔**: `test_mechanisms.py` 當天到 150/462 (32.5%, 天花板 33%), 而報這件事的守衛明寫「split at a seam, do not raise the constant」. 縫是**這個東西做什麼**: `test_mechanisms` 留下閘, 派工, trap 與表面 —— 會擋, 會路由, 會記錄的; 新的 `test_reporters.py` 拿走十個只算一個數字然後印出來的工具. 它們全部設計成 exit 0, 而那正是它們的測試該放在一起的理由: 對報表而言「它跑起來了」不是被測的性質. 分完 25.1%.

21 支 repo script 全部被套件引用, 抽查的多數確實被 `load_module` 或 subprocess 跑過 —— 但**不是 21/21**: `docs-size-report.py` 在整個 `main/claude/tests/` 底下只出現一次, 是 `test_contracts.py:1809` 的一行註解, 而 githooks 與 `sync.sh` 也不呼叫它. 它是唯一一支既沒有排程讀者也沒有自動執行者的報表, 所以它是 M2 候刪清單的第一個名字.
但「被套件跑過」和「有人讀它的輸出」是兩件事, 而**自動被讀**的只有: `contract-operator-delta` (git pre-commit 對暫存的 prompt-surface 檔印),
`sync.sh` / `merge-settings` / `merge-toml` (部署路徑), 以及 `weekly-integrity` 讀的三支部署 script.
其餘 17 支要有人記得跑.

**2026-09-08 量到並處理 (M2)**: 21 支裡有排程讀者的是 5 支 (`contract-operator-delta` 走 githook; `install-git-hooks`, `merge-settings`, `sync.sh` 走部署路徑; `merge-toml` 走 weekly). 其中只有 `contract-operator-delta` 是報表 —— 14 支報表裡 13 支沒有排程讀者. 處置不是把 13 支排進 `weekly-integrity`, 而是每支宣告自己的**觸發事件**; 候刪清單是空的.

`hook-system.md` 已經記過這個教訓的一次犯案 (「沒人讀的儀器不會告訴你它壞了」, 2026-08-20,
35,856 列裡只有 3 列是真的). 那次修的是**寫入端**; 讀取端到今天仍然是人力.

不主張把 17 支都塞進 `weekly-integrity` —— 那會把一份每週報告變成沒有人看完的長清單, 是同一個
失敗的另一種形狀. 主張的是**每支報表宣告自己該多久被讀一次**, 沒有答案的那幾支就是候刪.

### 缺口三: 依據的方向是單向的

程式碼指得到文件 (10/21 支 script 引用了 `docs/` 路徑; **09-08 更正**: 另外 10 支也解釋了自己, 只是指向姊妹腳本, 測試與事故日期, 所以「有依據」的真實比例是 20/21, 而 10/21 量的是引用形式不是依據有無), 文件指不回程式碼. 後果具體: 從證據那一側**列舉不出
「這份研究產生了什麼機制」**, 所以一份研究結論被推翻時, 沒有機械的方法找出哪些機制建在它上面.

現存的三份綜合文件都在證據那一側, 這就是為什麼它們答不了使用者這次問的後半句.

## 補讀之後的三條重新結論

初稿是先列舉機制再讀語料. 補讀六份研究文的結論段之後, 有三條要改, 兩條是降級.

### 一, M1 不是「fact-forcing 的前置」, 它就是主體 —— 而 fact-forcing 本身該降級

`trap-experiments` 的合計是 **37 個有效樣本, 實質陷阱 0 中招**; 失敗全部集中在格式 (強制行),
而每一種都被一句對症的措辭關掉. `landing-readiness` 的發現五據此寫下「再往實質防線加規則,
沒有證據支持」.

[ECC 計畫 Q3](../plans/upgrade-plan-ecc-2026-09.md) 的 fact-forcing **正是往實質防線加規則**.
兩者放在一起, 正確的讀法不是「所以不要做」, 而是:

```text
37 個 run 說   實質防線目前沒有可觀察的失效        →  加規則沒有依據
缺口一說       gate 層完全沒有行為資料             →  「沒有失效」也可能是沒在看
                                                    ↓
              先量現有那 7 個, 而不是先加第 8 個
```

**所以 M1 與 Q3 第一階段合併**, 且主體是 M1 (量現有 7 個 fail-closed gate 的真實命中), 不是 Q3
(為新守衛鋪路). 兩件事的差別在於: 如果兩週的資料顯示那 7 個幾乎不攔, 那麼 fact-forcing
連問題都沒有; 如果顯示常攔, 那麼**該修的是常攔的那幾支**, 而不是再加一支.

**這改變了 [ECC 計畫](../plans/upgrade-plan-ecc-2026-09.md)的排序**: Q3 從「最有價值但風險最高,
所以排最後」變成「依據被語料削弱, 併入 M1 之後才重新評估」.

### 二, 缺口二 (儀器沒有排程讀者) 的嚴重度下修, 因為尺度論證擋在前面

`resident-context-options` 的核心讀數是常駐字數只佔真實 prompt 的 **0.049% (p50)**, 而它的
「六分之一」那一節更進一步: 一個 session 收到的 skill 描述有 **79.4%** 不是本 repo 出貨的,
完全不在任何棘輪內, 而那一節明白寫了**不做成閘**的理由 (不是這一層付的成本, 就只報不擋).

同一條判準套到報表上: 17 支沒有排程讀者的報表, **它們的成本是人的注意力而不是模型的 context**.
所以 M2 (宣告讀取節奏) 的價值是**篩掉不該存在的報表**, 不是「讓更多報表被讀」——
把 17 支都排進 `weekly-integrity` 會製造一份沒有人看完的長清單, 那是同一個失敗的另一種形狀.
M2 的完成條件因此改成: **至少判定一支候刪**, 而不是「21 支都有宣告」.

### 三, 「量到的東西逐條不同」這一條, 讓本文的主表不能被讀成評分

`clause-pricing` 的 `m1` 量到一句話換掉觸發率三倍 (14/92 → 44/91, p = 0.0000014), 而
`wording-effect-scale` 用 30 個 run 證明那把尺**無法外推**到別的子句. 兩份合起來的一句話是:
**每條子句的效應要各自量, 量過的那條算數, 沒量過的不要借.**

本文主表列了「幾份文件提到這個機制」與「有沒有引用它服務的文件」. 那兩欄量的是**可發現性**,
不是效力. 一個被 21 份文件提到的機制 (`baton-dispatch`) 不因此比被 4 份提到的
(`test-first-change`) 更有依據 —— 前者只是被討論得多. **主表不是評分表**, 而初稿沒有把這句寫死,
現在寫在這裡.

## 這一輪之後該做什麼

七項, 兩項已經在別的計畫裡, 五項是新的. 全部**還沒落地**.

| # | 項目 | 依據 | 先紅的檢查 | 完成條件 |
|---|---|---|---|---|
| M1 | gate 層的第一批行為資料: 「只記錄不攔」, **對象是現有的 7 個 fail-closed gate 而不是新 gate** —— 記下每 gate 在真實 session 裡本來會攔幾次. **與 [ECC 計畫 Q3](../plans/upgrade-plan-ecc-2026-09.md) 第一階段合併, 且主體是這一項** (理由見[重新結論一](#一-m1-不是fact-forcing-的前置-它就是主體--而-fact-forcing-本身該降級)) | 缺口一 + `trap-experiments` 的 37/37 | — (觀察期) | 兩週的每 gate 命中數. **幾乎不攔 → fact-forcing 連問題都沒有; 常攔 → 該修的是常攔的那幾支, 不是再加一支** |
| M2 | 每支報表宣告讀取節奏 (每次 commit / 每週 / 每次上游重查 / 只在調查時), 沒有答案的列為候刪 | 缺口二 | `test_mechanisms` 新測試: 每支 `scripts/*.py` 的 docstring 要有一行節奏宣告; 今日 21 支全紅 | **至少判定一支候刪** (完成條件 09-08 改過: 原本是「21 支都有宣告」, 但那會誘人把 17 支全排進 `weekly-integrity`, 製造一份沒人看完的長清單 —— 理由見[重新結論二](#二-缺口二-儀器沒有排程讀者-的嚴重度下修-因為尺度論證擋在前面)) | **已完成 2026-09-08, 但完成條件沒達成**: 21 支各帶一行 `Read:` 宣告**觸發事件**, 由 `test_reporters.ReportCadenceTests` 釘住. 完成條件寫的是「至少判定一支候刪」, 而**一支都沒有** —— 逐支寫的時候每一支都答得出一個真的會發生的事件. 那是結果, 不是沒做到: 這條規則買到的是 21 個本來不存在的宣告, 加上下一支腳本進來時必須回答同一個問題. `Read: never` 這條分支仍然武裝著 (宣告 never 而沒有被任何盤點列為候刪就紅), 三向突變驗過. 落地當天 review 又抓到兩件, 同一個根因: `Read:` 一開始放在 `.py` 的 docstring 裡 (於是 16 支腳本的 `--help` 都多印一段, 而 argparse 摺疊段落讓它和下一段黏成沒有句界的長文), 在 `.sh` 裡則落在最後一個註解區塊的尾巴 (`sync.sh` 是一段講 bash re-exec 的技術旁白後面). **一個沒有人會看到的宣告不是宣告** —— 那正是這條規則要防的事, 而它自己先犯了. 改成一律放 shebang 下一行, 測試也從「前 40 行有沒有」收緊成「前三行」, 另加一支守衛斷言 `Read:` 不在任何 `__doc__` 裡. 順帶修掉規則自己的一個缺陷: 原本把 `whenever` 整個列為空話, 但「whenever a budget number is about to be raised」是事件 —— 一個分不出兩者的代理指標會為了看起來嚴格而擋掉好的那些.
| M3 | 反向索引: 每份研究文末列出「本文產生了哪些機制」, 或由腳本從程式碼的 docstring 反推生成 | 缺口三 | 先寫生成器 + 測試: 拿 `codename-gloss-report` 當校準案例 (它的 docstring 指向 `docs/README.md`, 反向索引要生得出這一條) | 生成的索引覆蓋 10/21 有引用的 script; 其餘 11 支要嘛補引用要嘛列為無依據 | **09-08 改形狀**: M4 的更正把它的地基抽掉了 —— 依據多半指向程式碼與事故日期, 不是 `docs/` 路徑, 所以「從 docstring 的 docs/ 引用反推索引」只生得出 10/21 而且漏掉的正是理由最厚的那幾支. 要嘛換成人工維護一張表 (那是本 repo 反覆拒絕的形狀), 要嘛接受索引只能覆蓋一部分並明說. **傾向後者, 但這一項改成先回答「反向索引要回答什麼問題」** —— 若問題是「這份研究被推翻時哪些機制受影響」, 那 docs/ 引用本來就是對的母體, 只是覆蓋率低要照實寫.
| M4 | 11 支沒有依據引用的 script 各補一行「為什麼存在」: `budget-drift-report`, `codex-prompt-census`, `denial-report`, `evidence-check`, `install-git-hooks`, `machine-state-check`, `merge-settings`, `merge-toml`, `prompt-surface-census`, `resident-pool-report`, `sync` | 缺口三 | 同 M3 的測試 | 每支一行, 指向真實存在的文件; 指不出來的那幾支要回答「那它憑什麼在」 | **已完成 2026-09-08, 而前提是錯的**: 打開那 11 支才發現 **10 支本來就解釋了自己為什麼存在** —— 只是引用的是姊妹腳本 (`prompt-surface-census.py` ↔ `resident-pool-report.py`), 測試檔, 與帶日期的事故 (2026-08-08 的證據引用失效, 2026-08-20 的 35,853 筆 fixture 汙染), 而不是 `docs/` 路徑. **我的探針量的是「有沒有引用 docs/ 路徑」, 那是「有沒有依據」的代理指標, 而且是個爛的.** 真正沒有理由的只有一支: `prompt-surface-census.py` 的 docstring 是一行空話. 已補上三段 (為什麼要確定性, 為什麼常駐桶比契約寬, 以及它刻意不量的另外六分之五).
| M5 | 7 個 fail-closed gate 各補一條推翻條件 (「什麼觀察會讓這個閘該被拿掉」) | 本文主表 | `test_deployment` 或文件測試: `hook-system.md` 的 fail-closed 表加一欄, 7 列都要非空 | 7 條都寫得出來; 寫不出來的那個閘就是候刪 | **已完成 2026-09-08**: 七條寫在 `docs/hook-system.md` 的「每個閘的推翻條件」節, 由 `test_deployment.GateRefutationTests` 釘住條數與**可觀察性**(不釘措辭: 每條要帶「連續」「超過」「從未」「改成」「改由」「開始」其中之一, 那分不出好條件與壞條件, 但分得出條件與心情). **七條都寫得出來, 所以沒有候刪的閘** —— 這是結果不是免檢. 三向突變全紅; 而突變當場抓到測試自己的三個缺陷: 子字串比對讓 `managed-target-guard-REMOVED` 照樣通過; 收緊之後 path-leaf 切分把 `githooks/pre-commit` 讀成 `pre-commit`; 只讀 bullet 第一行, 所以換行的條件被判定成沒有觸發條件. 三個都是掃描器錯不是文件錯.
| M6 | 跨上游整合第五輪: 把 ECC 的 11 條待採用放進[第四輪的計票表](cross-upstream-synthesis.md#第四輪整合-2026-09-06-開題與計票) | [ecc-survey](ecc-survey.md) | — | 每條標明是 ECC 自掙還是借來的 (血緣已在 ecc-survey 分過); 借來的不加票 | **已完成 2026-09-08**: [第五輪](cross-upstream-synthesis.md#跨上游整合第五輪-2026-09-08-第一個聚合型同業-以及計票規則的一次修訂) 開了, 只計 ECC 自掙的六條, 產出結論 10–12
| M7 | `landing-readiness` 重跑: 它覆蓋 18 份而今天有 21 份 (`ecc-survey`, `task-observer-upstream`, 它自己沒進去), 且 08-31 之後 8 份研究文與 3 份計畫動過 | 本文覆蓋率節 | — | 覆蓋率表更新到 21 份; 或判定「四項建議全結案且沒有新候選」而不重跑 | **已完成 2026-09-08**: [重跑節](landing-readiness.md#2026-09-08-重跑-21-份-而落地順序沒有改變) —— 覆蓋率 18→21, 四項建議全結案, **新候選零**, 而發現五的樣本數從 67 更正為 37

排序理由: M2 與 M4 是純文件與測試, 最便宜; M5 逼出的是判斷不是程式; M3 要先有 M4 的資料才生得出
完整索引; M1 要跑兩週所以最早開始但最晚結案; M6 與 M7 是盤點性的, 沒有被前面幾項擋住.

## 沒有做的

- **13 份研究文只讀骨架**, 沒有重讀結論段. 所以「依據夠不夠強」多半是繼承而不是複核.
- **skill 與 role 兩類沒有做反向掃**, 只有 script 與 hook 做了. 那兩類的「0 引用」若存在, 本文看不到.
- **沒有評估任何一個機制該不該存在.** 本文只問「它站在什麼上」, 不問「它值不值得」——
  後者要 M5 的推翻條件先寫得出來.
- **`landing-log` 系列 (4.6 萬字) 沒有讀.** 與 `landing-readiness` 同一個盲區, 兩輪都沒解.
- **115 這個數字不含**: 契約檔本身, `settings.json` 與 `model-routing.toml` 這類真相源,
  githooks 以外的 git 設定, 以及 memory 目錄.

## 推翻條件

- **M4 的 11 支裡有任何一支答得出「它服務的文件是哪份」而我只是沒掃到** → 缺口三的規模下修,
  但方向性 (文件指不回程式碼) 不變, 因為那是分開量的.
- **`evals/` 出現第一個瞄準 gate 的情境** → 缺口一結案, M1 改成「已經有一個, 還缺幾個」.
- **M5 的 12 條推翻條件裡有超過三條寫不出來** → 那不是文件缺陷, 是那幾個閘本來就沒有停止條件,
  該進的是候刪清單而不是文件待辦.
- **`landing-readiness` 重跑後結論與 08-31 相同** → M7 結案, 並記下「四週的語料增量沒有改變落地
  順序」, 那本身是一筆關於重跑節奏的證據.
