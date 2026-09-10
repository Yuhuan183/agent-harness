# ECC 勘查後的升級計畫

2026-09-08 起. 這一頁擁有的是**排程與完成條件**; 每一項為什麼採用, ECC 的原文在哪, 查了什麼才
這樣判, 全在 [ECC 勘查](../research/ecc-survey.md). 這裡不重述依據, link, don't repeat.

**本頁上的每一項都還沒落地.** 本 repo 的常規是採用與實作同一輪完成, 否則紀錄會說謊; 這一輪
使用者要的是報告與計畫, 所以勘查表用「待採用」而不是「採用」, 而這一頁的完成條件欄一律是未來式.
任何一項真的落地時, 在勘查表把該列改成「採用」或「改造後採用」, 並在本列補上當天的量測數字 ——
**兩處同時改, 不然就是本 repo 自己警告過的那種「寫在落地之前的處置」**.

背景一句: ECC 是走相反方向的同業 (要覆蓋面, 不要最小規則集), 42 條規則裡 11 條本專案沒有等價.
其中兩條是它自己撞出來的教訓 (拒絕文字重複會讓模型退化, 加了欄位卻沒加讓欄位過期的測試),
一條是它借來但寫得最好的守衛工程 (掃描器對看不懂的形式直接失敗).

## 2026-09-08 晚間重新結論: 語料讀完之後, 三項移位

這一頁的初稿是在勘查完 ECC 之後直接排的, 沒有先走過本 repo 自己的語料. 同日補做的
[全語料重跑](../research/landing-readiness.md#2026-09-08-重跑-21-份-而落地順序沒有改變)與
[機制側盤點](../research/mechanism-evidence-map.md)之後, 三項要移位, 兩項是降級.

| 項目 | 初稿排在哪 | 現在 | 為什麼 |
|---|---|---|---|
| **Q3 / Q3b** (fact-forcing) | 最後, 但標成「本輪最有價值的一條」 | **併入 [M1](../research/mechanism-evidence-map.md#這一輪之後該做什麼), 且主體是 M1** | `trap-experiments` 的 37 個有效樣本實質陷阱 0 中招, 語料明文寫「再往實質防線加規則沒有證據支持」. fact-forcing 正是那種加法. 先量現有 7 個 fail-closed gate, 而不是先加第 8 個 |
| **Q4** (SessionStart 上限) | 「先量再決定」 | 不變, 但**預期結論改成不加** | 常駐字數只佔真實 prompt 的 0.049% (p50), 而 SessionStart 注入是每 session 一次不是每回合 —— 它的成本比那個數字更小. 值得量的是「finding 太長會不會擠掉別的」, 不是省 token |
| **Q9b** (數字住在 prompt 表面) | 最後一列, 一句話 | **提前, 而且理由變強** | `m1` 量到一句話換掉觸發率三倍, `wording-effect-scale` 量到那把尺無法外推 —— 合起來是「每條子句的效應各自量」. 一個未經校準的效果數字放在 skill description 裡, 就是一條沒量過而被當事實引用的子句 |

**沒有移位的**: Q1 (環境開關雙向文件), Q2 (拒絕訊息衰減), Q5 (部署矩陣過期測試),
Q10 (skill 出處行) —— 四項都不碰實質防線也不碰常駐預算, 語料對它們沒有話說, 排序照舊.

### 這一頁提到的閘

下面幾項的量測數裡點名了個別的閘. 為免讀者把那些片段當成清單, 完整的一份在這裡, 而它的擁有者是 [`docs/hook-system.md`](../hook-system.md):
`commit-test-gate`, `push-consent-gate`, `leaf-redispatch`, `runtime-guard`, `verifier-quota`, `managed-target-guard`, 以及 git 側的 `githooks/pre-commit`.

git 側那一支涵蓋的是文字層推測不到的路徑, **不是所有路徑**: `--no-verify` 與 `-c core.hooksPath=` 都繞得過去, 真正關得起來的那一層是 CI.

## 排程怎麼排

每項照本 repo 自己的規矩走: 改行為的規則先寫會紅的檢查; 新守衛先量三個數 (今日命中, 真缺陷,
正規化) 再兩向突變; 落在一個 provider 的規則落到雙生; 動到 prompt surface 就重跑 census 並位移
預算. 順序按「最便宜且擋住信任的先」:

```text
    純測試 (已有量測)      追蹤缺口          行為改變 (已有量測)     先量再決定        prompt surface
    -----------------      -----------       --------------------    --------------    --------------
 Q1 環境開關雙向文件  ─→  Q9 pin-report ─→  Q2 拒絕訊息衰減    ─→  Q4 注入上限   ─→  Q8 記憶輪替
    (6 命中/3 真缺陷)      同業列             (18 連擊實測)          (預期不加)        Q8b 平台 no-op
 Q5 部署矩陣過期測試                          Q6 Skill 失敗遙測      Q7 守衛設定       Q9b 數字住在
 Q10 skill 出處行                                                                          prompt 裡

 Q3 / Q3b 已於 09-08 併入機制盤點 M1 (先量現有 7 個 fail-closed gate, 不先加第 8 個) —— 見上一節
```

Q1 與 Q5 先, 因為兩者都是純測試, 不改任何執行期行為, 而且 Q1 的三個數已經量過了.
Q3 排最後且**先做只記錄不攔的版本**: 它是本輪最有價值的一條, 也是唯一會改變每一次編輯行為的一條,
沒有本機誤報率就加閘等於發一張「請忽略這個測試」的邀請函.

## 十項 (含三個子項)

| # | 項目 | 來源與血緣 | 先紅的檢查 | 落地面 | 完成條件 |
|---|---|---|---|---|---|
| Q1 | hook 讀的每個 `AGENT_*` 環境開關都要在 `docs/hook-system.md` 有名字, 且反向也成立 (文件寫了但沒人讀的要紅); 掃描器對它看不懂的存取形式**直接失敗**而不是略過 | ECC `tests/ci/gateguard-env-documented.test.js` (ECC 自掙, issue #2573) | `test_deployment` 或 `test_mechanisms` 新測試: 現在應該紅在 3 個真缺陷上; 把 `AGENT_HARNESS_REPO` 補進文件後只剩 2 | `main/claude/tests/`; 不動 prompt surface, 無預算 | **三個數已量 (2026-09-08)**: 今日命中 6 (`AGENT_EXPERIENCE_LEDGER`, `AGENT_EXPERIENCE_LOG_BIN`, `AGENT_EXPERIENCE_PENDING`, `AGENT_HARNESS_PYTHON`, `AGENT_HARNESS_REPO`, `AGENT_RUNTIME_VERSION`) / 真缺陷 3 (`AGENT_HARNESS_PYTHON` 被攔截訊息當成修法指名卻沒進文件; `AGENT_HARNESS_REPO` 會換掉 `managed-target-guard` 認定的來源 repo; `AGENT_RUNTIME_VERSION` 能改 `weekly-integrity` 報出來的版本) / 正規化「套件與 replay 專用的覆寫不算, 它們屬於測試而不屬於操作者」—— `AGENT_EXPERIENCE_*` 三個只在 `lifecycle-replay.md` 出現, 要嘛允許那份文件計數, 要嘛列白名單. 落地時: 兩向突變 (拿掉一個文件裡的名字看它紅), 且 Python 側要有等價的「看不懂就失敗」條款 (`os.environ.get` 以外的形式). **已完成 2026-09-08**: 測試先紅在**正好那六個名字**上再綠 —— `test_deployment.HookEnvDocumentationTests` (6 支). 三個數確認: 命中 6 / 真缺陷 3 / 正規化「不是排除套件專用的覆寫, 是**全部都寫進文件**」—— 一個只有測試在用的覆寫仍然是這台機器上真的會被讀的東西, 而『它只有測試在用』是註解該說的話, 不是省略它的理由. 兩向都釘: 正向嚴格 (只算真讀取, 註解與錯誤訊息裡的名字不算), 反向寬鬆 (只問這個開關還在不在, 因為 `AGENT_SKIP_TEST_GATE` 根本不是環境讀取而是指令前綴, 嚴格的反向會要求把它從文件裡刪掉). 掃描器解一層模組常數 (`ENV = "AGENT_X"`), 其餘間接形式**直接報失敗而不是略過**. 四向突變全過 (拿掉文件裡一個名字 → 正反兩支各自紅且指名; 在 hook 裡加一個解不開的鍵 → 可追蹤性守衛紅; 加一個沒文件的字面讀取 → 正向紅), 還原後綠. 落在 `test_deployment` 而不是 `test_mechanisms`: 後者被自己的 sprawl guard 擋下 (它已是 4,854 行), 而那道 guard 明寫「split at a seam, do not raise the constant» —— 縫就是 `MachineStateHygieneTests` 那兩支同主題的 doc↔code 守衛. Codex 沒有 hook 目錄, 所以沒有雙生要落. |
| Q5 | `deployment-manifest.tsv` 的每一列補「驗證指令」與 `last_verified`, 並**同時**加讓它過期的測試 | ECC `harness-adapter-compliance.js` 的欄位設計 (採形狀), 加上它自己的失敗 (三個 `last_verified_at` 最舊離 HEAD 四個月, 全 repo 沒有測試) | 新測試: fixture manifest 帶一個 400 天前的日期要紅; 今日 40 列全部沒有該欄, 所以第一次跑必紅 | `scripts/deployment-manifest.tsv` + `main/claude/tests/test_deployment.py`; manifest 不是 token surface | 過期門檻要先決定 (**DECISION 待定**: 90 天還是跟著 `weekly-integrity` 的既有節奏); 兩向突變 (把一列日期改舊看它紅); **這一項的重點是那個測試, 不是那個欄位** —— 沒有測試的欄位就是 ECC 現在的狀態 |
| Q10 | 每支 skill 帶一行出處: 有上游的指向 `ATTRIBUTION.md`, 沒有的明寫「本專案自有」 | ECC 的 `origin:` frontmatter 欄 (覆蓋率 286/286) | `test_ledger` 或 `test_contracts` 新測試: 今日去重後 12 支 skill 只有 5 支有 `ATTRIBUTION.md` (baton-dispatch, evidence-debugging, readable-zh-tw, task-observer, test-first-change), 其餘 7 支沒有任何出處宣告, 第一次跑必紅. **母體要去重**: 三個 provider 樹共 24 個目錄條目, 多數是指向 `.agents/skills` 的 symlink | 兩個 provider 的 skill 目錄都在母體裡; 若寫進 frontmatter 就是 **prompt surface**, 要重跑 census 並位移預算 | **DECISION 已定**: 放 skill 目錄下的獨立檔, 沿用既有的 ATTRIBUTION 形狀, 不動 prompt surface. **09-08 重新定範圍, 沒有落地**: 那 7 支**不是沒有出處**, 是出處寫在研究文的散文裡而不是 `ATTRIBUTION.md` —— 七支每一支都在多份研究文裡出現, 其中 `leaf-dispatch` 落在 `peer-harnesses.md` 與 `mattpocock-skills-integration.md`, 很可能真有上游. **所以這一項不是補一行, 是替 7 支各做一次溯源**: 從 21 份文件的散文裡判定它到底有沒有上游, 判錯的代價是實的 —— 對一支其實蒸餾自別人的 skill 寫「本專案自有」是假聲明, 而且會讓 `upstream-pin-report` 的推導繼續看不見它. 這是 upstream-distillation 的工作量, 不是文件雜務. **下一步**: 先只做 `leaf-dispatch` 一支當樣本, 量出「一支要多久」再決定其餘六支排不排. |
| Q9 | `upstream-pin-report.py` 也讀 research README 裡帶完整 SHA 的**同業**列, 讓 ECC 這種「查過但沒蒸餾」的來源也被機械追蹤 | 本輪自己撞到的缺口 (`upstream-pin-report.py:97-111` 明寫只撿上游列) | 先寫測試: fixture README 加一列同業帶 SHA → 現在不會被撿, 改後會 | `scripts/upstream-pin-report.py`; 無預算 | 要先解掉 eli5 那種 **path commit 不是 repo head** 的誤判 —— 否則報表會說一個沒動的 repo 動了. 可能的作法: 同業列另立一欄或另一個標記, 由列自己宣告 SHA 指的是什麼. 完成條件: 加了 ECC 那列後報表多一筆且 eli5 那列**不**被撿. **已完成 2026-09-08**: 測試先紅 (真實索引裡沒有 `affaan-m/ecc`) 再綠. **解法比原本設想的小**: 不需要新欄位也不需要新標記 —— eli5 的 SHA introduced by 「path 最後 commit 仍是」, ECC 的 introduced by 「pin `<sha>`」, 兩者本來就寫得不一樣, 所以拿掉 `類別` 過濾之後 `PIN_CELL` 自己就分得開. **判準因此從欄位換成句子**: `pin `<sha>`` 是對整個 repo 的宣稱, `path 最後 commit 仍是` 是對一個目錄的宣稱, 只有前者比得起來; 而寫列的人可以刻意滿足前者, `類別` 欄從來不行 (它說的是這個來源對我方是什麼, 不是它的 SHA 是什麼意思). 兩向突變都過: 把 ECC 那列改寫成 path commit → 它不再被追蹤且測試指名它; 把 eli5 那列改寫成 head pin → 它開始被追蹤且測試指名它. 實跑 7 個 pin (原本 6), ECC 讀 `current`; 同日順帶看到 sepia `MOVED +22`. 落在 `test_reporters.py` —— 見同項下方的分檔註記. |
| Q2 | 拒絕訊息衰減: 同一 gate 在同一 session 連續攔截時, 前 N 次發完整訊息, 之後改單行並帶本 session 序號, 讓連續拒絕永不逐字相同 | ECC #2142 (ECC 自掙的獨立觀察), 機轉見 `gateguard-fact-force.js:934-948` | 先寫測試: 對同一 gate 連送三次同樣的攔截輸入, 斷言第三次的 stderr 與第一次**不相同**; 今日必紅 | `main/claude/hooks/denial_log.py` 是共用點, 但訊息在各 gate 裡 —— 傾向讓 `denial_log.record()` 回傳序號, 各 gate 自己決定要不要縮 | **三個數已量 (2026-09-08, `scripts/denial-report.py`)**: 最長連擊 `commit-test-gate` 18 (結束 2026-09-04; git 側對應的 `githooks/pre-commit` 不寫 denial 列, 拿不到 payload), `managed-target-guard` 5, 其餘 1. 真正逐字相同的是 `managed-target-guard` 與 `push-consent-gate` (訊息全靜態); `commit-test-gate` 的 `suite-red` 帶 15 行 stderr 尾巴, 同一個測試一直紅時才逐字相同. 所以**先做的是那兩支靜態訊息的 gate**, `commit-test-gate` 列為第二階段. ECC 的預設 N=3 直接沿用還是重挑, 落地當天決定並寫在這裡. **已完成 2026-09-08**: 測試先紅在「第四次拒絕與第一次逐字相同」上再綠. `denial_log.record()` 現在回傳本 session 的序號, 前三次發完整訊息, 之後單行帶 `#N`. N=3 沿用 ECC 的預設 —— 本機連擊 18 與 5 都夠長, 任何小的 N 行為相同, 沒有理由另挑. **只做了 `managed-target-guard` 一支, 沒有做 `push-consent-gate`**: 後者量到的最長連擊是 1, 衰減沒有對象, 而替一個從沒連續攔過的閘加一條永遠不跑的分支, 正是本 repo 對 leaf-redispatch 寫的那條推翻條件在講的事 (死碼比沒有碼更糟). 共用機制已經在, 那支要用時是一行. 四向突變全紅, 其中兩個是安全方向: 序號算不出來時改成condense → fail-open 後備破掉; 跨 session 計數 → 新 session 繼承序號. 另兩個是行為方向: 永不 condense, 以及 condensed 訊息拿掉序號 (那會讓連續的短訊息彼此逐字相同, 是原本的失敗往後挪一步而不是修掉). |
| Q6 | Skill 硬失敗留痕: `PostToolUseFailure` 或等價事件上記一行, 讓「哪支 skill 常載入失敗」數得出來 | ECC `hooks/hooks.json` 的 `PostToolUseFailure[Skill]` 條目 (ECC 自掙) | 先確認本機 client 有沒有這個事件 —— **這是前置條件, 不是實作步驟**; 沒有就整項不做 | `main/claude/hooks/`, 沿用 `denial_log` 的「只記識別欄位不記內容」形狀 | 本 repo 已有的教訓要一起帶: 記錄失敗絕不影響主流程 (fail-open 簿記), 且套件不得寫進開發者本機那一份 (`AGENT_DENIAL_LOG` 的同一條理由). 完成條件: 事件確認存在 → 一支 fail-open hook → 一次真實 Skill 失敗被記到. **前置條件已答 (2026-09-08): 成立.** client 2.1.263 的事件表含 `PostToolUseFailure`, 而且本機 `~/.claude/settings.json` 與 `settings.local.json` 已經各有一支第三方 hook (rtk 與 Orca) 掛在上面, matcher `*`. 順帶看到 client 認得的事件比本 repo 註冊的多五個: `PermissionRequest`, `PostCompact`, `StopFailure`, `TeammateIdle`, `UserPromptSubmit`. **但實作還沒開始**, 而且要先回答一個本項自己的問題: 本 repo 至今沒有任何 Skill 硬失敗的事故資料, 所以這是「先收資料再談要不要用」—— 與 `denial_log` 2026-08-08 的立項理由同形, 那是本 repo 支援的順序, 但值得在落地時明說一次. |
| Q4 | SessionStart 注入內容的上限與截斷標記 | ECC `session-start.js:39,197-208` (預設 8,000 字元) | 先量: `compact-reseed` 今日注入 297 B; `weekly-integrity` 今日 0 B (節流戳記 `~/.claude/telemetry/.integrity-last-run` 是 2026-09-07), **未節流時的篇幅本輪沒量到** | `main/claude/hooks/weekly-integrity.py`; 注入內容是 prompt surface 的一種, 但不在 census 母體裡 (census 管的是檔案) | 先量未節流時的 finding 篇幅 (刪戳記或以暫時 HOME 跑一次), 有數字才決定要不要上限. **如果最壞情況也只有幾百位元組, 這一項就是「量過, 不加」** —— 那也是結案. **09-08 重新框**: 預期結論是不加 —— 常駐只佔真實 prompt 的 0.049% (p50), 而 SessionStart 是每 session 一次. 值得量的是擠不擠掉別的, 不是省 token. **已量, 全域上限不加, 但綁了一段 (2026-09-08)**: 刻意在漂移最多的一次量 —— 拿掉節流戳記直接跑一次 (量完還原, mtime 也還原), **1,600 B / 18 行**, 是 ECC 8,000 字元預設的五分之一. 全域上限因此不加: 常駐只佔真實 prompt 的 0.049%, 在這個尺度上為了省位元組去截斷一個真的訊號, 換到的是零. **但量到一段是無界的**: 每個未對帳的 dispatch 各印一行, 而且會一直印到有人對帳為止, 所以這一條 finding 一行一行長, 沒有天花板. 綁的是**列舉**不是尺寸, 而這個差別就是重點 —— 操作者要的數字是「有多少沒對帳」, 所以總數照寫, 只把清單縮成前 10 筆加「... and N more」. 一個會弄丟總數的截斷, 比它取代的長清單更糟. 落地後實跑: 今天 11 筆, 顯示 10 加 1, 1,643 B (多的 43 B 是那個總數, 那正是要留的東西). 三向突變全紅, 而第三個突變抓到測試自己的缺陷: 強迫短清單走截斷分支時 id 全都還在, 所以只斷言 id 存在的測試看不見它印出「3 of them, oldest 10 shown ... and -7 more」. |
| Q7 | 守衛的設定不得被調鬆以求綠: 動到測試裡的上限表, 預算數字, `evidence-check.py` 的規則時要留痕或要理由 | ECC `config-protection.js` (擋 linter/formatter 設定) 的**改造版** —— 本 repo 沒有 eslint, 等價物是自己的閾值 | 先量: 過去 N 個 commit 裡有幾次同時改了「上限數字」與「使測試變綠」; 沒量到就不做 | 可能是 githook 而不是 Claude hook (它要看的是 diff, 不是單次 Edit) | 這一項最可能的結論是**不做**: 本 repo 的預算調整本來就要求「帶量測與理由」並寫進 landing-log, 已經是同一條規則的社會版本. 完成條件是那個量測數字, 不是那個守衛. **量過, 不加 (2026-09-08)**: 推翻條件成立. 掃過去 200 個 commit, 動到 `test_contracts.py` / `support.py` 裡三位數以上常數或 `*_CEILING` 的有 **16 次**, 而 **16 次全部**在 commit message 裡帶了理由 (量測數字, 位移對象, 或 `because`). 沒有一次是「調鬆以求綠」. 所以那道守衛沒有要防的行為 —— 本 repo 現行的社會規則(預算調整要帶量測與理由並寫進 landing-log) 已經在做同一件事, 而且做到了. **推翻條件**: 出現一次動了上限而 commit message 說不出理由的; 那時再談守衛. |
| Q8 | 記憶輪替規則: 不可信輸入 (抓取的網頁, 第三方 repo, 附件) 之後, memory 的寫入要另外標記或不寫 | ECC `the-security-guide.md:339-352` (它借自 Anthropic 對 memory 載入時機的說明 + Microsoft 的推薦污染報告, **不是它自己的觀察**) | 「不可信 run」的定義要先寫得出來, 寫不出來就是偏好不是規則 | memory 契約在 client 的 prompt 表面, 動它要重跑 census 並位移預算 | 本輪就是一個活例子: 這次讀了一整個第三方 repo. 完成條件: 定義寫得出來 → 一句進 memory 契約 → census. 定義寫不出來就記「不做」與理由 |
| Q8b | 逐機制的平台宣告位: 「此機制在此平台上等於沒有」要有地方寫, 且連續失敗 N 次後出聲 | ECC `continuous-learning-v2` 對 Windows observer 的宣告 (附 issue #2489) | — (文件) | `docs/hook-system.md` 的「這套設計的邊界」節底下 | 本 repo 目前只有整體邊界節, 沒有逐機制欄. 完成條件: 現有 12 支 hook 各有一句「在什麼條件下等於沒有」, 至少一句不是「無」 |
| Q3 | fact-forcing: 每檔第一次 Edit/Write 要求交出 importer, 受影響 API, 資料 schema, 使用者指令逐字引用 | zunoworks/gateguard (經 ECC), 機轉見勘查的[證據等級節](../research/ecc-survey.md#證據等級-形狀可借-數字一律不借) | **第一階段只記錄不攔**: 一支 fail-open hook 記下「這是本 session 對這個檔的第一次寫入」, 跑兩週, 得出「一天會攔幾次」 | `main/claude/hooks/`; 若成閘則要雙生 | 三個數要在第一階段之後才拿得到. **ECC 的 +2.25 分不採信** (n=2, 主觀分, 無 rubric). 若要證明效果, 用本 repo 自己的 replay: 一臂帶閘一臂不帶, 量成本與交付綠. 完成條件: 第一階段的命中數 → 決定要不要有第二階段. **09-08 移位**: 併入[機制盤點 M1](../research/mechanism-evidence-map.md#這一輪之後該做什麼), 主體是 M1 而不是這一項; 理由是 `trap-experiments` 的 37/37.  |
| Q3b | 破壞性 shell 指令的 fact-forcing (影響清單 + 一行回滾 + 逐字指令) | 同上 | 同上, 併在 Q3 第一階段一起量 | 同上 | 本專案已在 `git commit` 與 `git push` 兩點設閘, 這一項要回答的是「還有哪些指令值得」. 若第一階段量到的破壞性指令幾乎都已被現有兩個閘涵蓋, 結論就是不做. **09-08 移位**: 同 Q3, 併入 M1 的觀察期.  |
| Q9b | `evidence-ladder` 補一句: 未經校準的效果數字**住在 prompt 表面上**時 (skill description, agent description) 風險更高, 因為模型會把它當事實引用 | ECC gateguard 的 `description` 欄是活例子 | `test_contracts` / `test_ledger` 對該 SKILL.md 的片語斷言 | **prompt surface**: `scripts/prompt-surface-census.py --write`; `docs-size-report.py` 與 `budget-drift-report.py` 先量, 位移或帶理由的上調 | 一句話, 不是一節. 位移目標: 該 skill 現有的數字相關段落. 完成條件: census 過, 預算數字與理由寫進 landing-log. **已完成 2026-09-08**: 一行進 `evidence-ladder` 的第 2 節數字條目 —— 「A number in a `description` is read every load; put it at L5 or drop it, never merely cite it.」 **預算沒有位移也沒有上調**: 1,271 → 1,292 字, 上限 1,295, 剩 3 字. 那不是設計, 是運氣 —— 下一個要動這支 skill 的人得先位移. census 重寫過 (`--write` 要帶路徑, 不是旗標). |

## 明確不做的 (依據在勘查表各列)

- **四份常駐檔的拆法 (A1), prompt-defense baseline (A2), 80% 覆蓋率門檻 (A8)**: 都是加規則不加
  可失敗的檢查; A1 更是本 repo 已經走過的反方向.
- **instinct 信心分數與 `/evolve` 叢集 (C1, C5)**: 信心分數是模型自評的另一種寫法, 沒有校準來源;
  本專案的 skill 是蒸餾產物不是生成物.
- **`harness-audit` 式的評分 rubric (D2)**: 打分會製造「分數上升即改善」的假訊號.
- **安裝 profile (F2), 多語系鏡像 (F3)**: 兩者都把「現在是什麼狀態」變成要對帳的東西;
  F3 在 ECC 已經長成 1,394 個沒有同步檢查的過期面.
- **擋 `--no-verify` (B7)**: 分歧不是疏漏, 理由與推翻條件在勘查的[兩個分歧](../research/ecc-survey.md#兩個分歧)節.
- **hook profile 分級 (B8), 治理事件另開一條 (E5), process group kill 與心跳 (E3)**: 形狀不同或
  沒有對應的執行面.
- **MCP 斷路器 (B11), per-skill 健康度 (D1)**: 記為缺口但不排 —— 兩者都沒有本機事故或語料,
  沒有資料就加閘是本 repo 反覆說過不做的事.

## 推翻條件

- **Q1 的三個數在落地當天重量後真缺陷變成 0** → 不加測試, 把數字留在該列, 該列改成「量過, 不加」.
- **Q2 落地前最長連擊掉到 3 以下** → 衰減沒有對象, 整項改成「量過, 不加」.
- **Q4 量到未節流的注入篇幅只有幾百位元組** → 不加上限, 記數字結案.
- **Q7 量到過去的預算調整都帶了理由** → 守衛不做, 只在 landing-log 記那個數字.
- **Q3 第一階段兩週命中數低到不值得** (例如一天 1 次以下) → 不做第二階段, 而那個數字本身回答了
  「本專案的編輯行為要不要被強迫調查」.
- **`upstream-pin-report.py` 因為 ECC 的更新頻率 (一天 26 個 commit) 而讓 pin 比對失去意義** →
  Q9 的價值降到只剩「提醒該重查了」, 那時改用查核日而不是 SHA.
