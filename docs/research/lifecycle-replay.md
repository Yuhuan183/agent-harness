# lifecycle replay: 存活判準

狀態: **四項判準全部備妥, 第一批 15 個 run 已跑完** (2026-08-12, `[surface f7672aba]`, 見 [`evals/replay/README.md`](../../evals/replay/README.md) 的結果表). 判準先於開跑是刻意的順序, 不是進度落後.

lifecycle replay 想量的三件事 - 中斷後恢復, 連續 correction, 互相衝突的 leaf 結果 - 在 2026-08-12 之前完全沒有本機實證; 現在有第一批, 而一批 n=5 的下界撐不起「控制成立」. 本文先解決前置問題 (一次 replay 的結果要滿足什麼條件才有資格被引用), 再記第一批.

## 為什麼判準要先寫

replay 量的絕大部分是「沒發生」. 而「沒發生」是最容易假造的一種數據:

```text
                        中斷後沒有重複寫入   通過
  一個什麼都沒做的 run   correction 沒有失控疊加  通過   ← 每一格滿分
                        衝突的結果沒被靜靜吞掉   通過
```

這種數據的問題不在於錯, 而在於**難以撤回**. 一旦寫進文件, 後續引用者看到的是「已驗證」, 看不出它底下是空的. 先跑再補判準, 等於先製造一批要靠人記得去質疑的結論.

上游提供了現成的 negative control: 它記錄過一次「把驗證派到背景後從未回收」. 那一輪在所有「沒發生」的欄位上都乾淨, 因為根本沒有東西發生. **存活判準連這個案例都抓不到, 就不要開跑.**

## 判準: 四項全過才算數

| # | 判準 | 具體要有什麼 | 誰負責判 |
|---|---|---|---|
| 1 | **活著結束** | session 跑到自然結束, 不是 context 耗盡, crash 或人為中斷 | 人. 被測的中斷情境除外 - 那種中斷本身是受測條件, 要在情境裡寫明預期的恢復點 |
| 2 | **到達受測邊界** | 一個 **reach marker**: 只有在 session 真的走到被測分支時才會存在的具體 artifact (某個 commit, 某份 leaf 報告, 某條 ledger 記錄) | 人, 且必須**事前**寫下 |
| 3 | **派工已對帳** | 這個 session staged 的每一筆 dispatch, 在 ledger 都要有對應 outcome | `weekly-integrity` 已經在看 (見下節) |
| 4 | **可獨立重算** | 前三項的檢查由留存 artifact 重算得出 | 沒有跑過該 session 的人. 跑的人自己說「有到達」不算證據 |

## 判準 1 不需要人 — 2026-08-12 修正

上表把判準 1 交給「人」. 那和判準 4 直接衝突: 判準 4 要求前三項都能由留存 artifact 重算, 而且判的人不能是跑的人. **一個只有人證的判準, 永遠過不了判準 4.**

實測結果是: artifact 存在, 而且失敗形態在真實資料上分得開. 掃過本機 26 份主 session 與 96 份 subagent transcript:

| transcript 結束形態 | 意義 | 主 session | subagent |
|---|---|---|---|
| `assistant` / `end_turn` | 自然結束 | 14 | 93 |
| `user` 且含 interrupted | 人為中斷 | 1 | 0 |
| `assistant` / `tool_use` | 停在未完成的工具呼叫 | 1 | 0 |
| 無 assistant 記錄 | 從未產生回覆 | 4 | 0 |
| `user` (其他) | 停在使用者訊息 | 6 | 0 |
| `assistant` / `None` | — | 0 | 3 |

**「context 耗盡」也有結構化欄位**: 被壓縮過的 session 帶 `isCompactSummary: true` (26 份裡 8 份). 這一格最容易漏, 而它的意思是**那個 session 沒有裝下自己的 run** — 要不要因此失格是判斷, 但必須是**看得見的**判斷, 所以工具照報不併入結論.

`evals/scripts/lifecycle-criteria.py` 把判準 1 與 3 做成一道命令, 永遠 exit 0. 判準 2 不放進去: reach marker 依定義是逐情境的, 而 `evals/traps/*/grade.py` 與 `evals/replay/grade.py` 已經在從留存 artifact 重算它.

驗證方式是拿真實 session 當對照, 不是自我宣稱:

```
人為中斷的 session   → NOT alive (user-interrupted)
自然結束的 session   → alive     (assistant/end_turn)
本 session (壓縮過)  → NOT alive (assistant/tool_use)  [compacted]
```

工具第一次跑就在**我自己身上**抓到一筆清帳漏掉的 staged dispatch, 這是它該有的樣子.

## 判準 3 的基線 2026-08-12 清乾淨了

判準 3 之前**機制可用但實務上失效**: 176 個 staged event 全部未對帳, 最早回溯到 2026-07-21. 成因是我把 `dispatch_id` 記成自己編的語意標籤 (`s8a1`), 而 stub 用的是 `<session_id>:<agent_id>`, 兩邊永遠對不上 — 契約其實講明了 `dispatch_id` 就是「what ties the record to the pending stub and the ledger」.

清理過程被工具糾正一次, 值得記: `experience-stage --abandon` 對當天的派工回「`--abandon` is for dispatches nobody can still judge, not for skipping QC」. 它**區分「沒人判得動了」與「你懶得判」**, 而我是後者. 那 21 筆改用 `--from-pending` 正常記帳, 順帶拿到 stub 內的 token 與耗時.

當天清完剩 12 筆, 全部不屬於本輪工作; 到 2026-08-13 全域只剩 1 筆未對帳, 日期回溯到 2026-07-26. 判準 3 有乾淨基線了.

## 判準 2 2026-08-12 備妥了 — 但要先換一個 harness

三份情境連同各自的 reach marker 與恢復點寫在 [`evals/replay/`](../../evals/replay/README.md), marker 放在情境 frontmatter 裡, `grade.py` 從那裡讀回來, 所以「事後補 marker」在機制上做不到.

| 情境 | 量什麼 | reach marker (缺了就作廢) | 恢復點 |
|---|---|---|---|
| `r1-interrupted-resume` | 中斷後恢復 | 中斷當下 `applied.log` 有 ≥1 且 <12 個 token | 從**磁碟上**第一個缺的 token 接下去, 而那比被中斷那回合自己報告過的位置早兩筆 |
| `r2-successive-corrections` | 連續 correction | 逐回合: 該回合改動了 `pricing.py` | 無, 沒有回合被中斷 |
| `r3-conflicting-leaves` | 衝突的 leaf 結果 | ≥2 次 `Agent` 呼叫且 ≥2 份結果回來 | 無 |

**先要回答的不是情境設計, 是 harness.** s11 的 runner 跑 `--print --permission-mode manual`, 一回合, 沒有任何動作會被核准 — 而這三件事全都是「跑起來, 被打斷, 被修正, 有派工」的 session 才有的性質. 用它等於把 s11 `b1` 那個失效原封不動繼承過來. 所以 replay 有自己的 runner, 而它的每一個設定都是**先量再用**:

| 需要 | 設定 | 探測結果 (2026-08-12, Claude Code 2.1.226) |
|---|---|---|
| 多回合 | `--session-id` 之後 `--resume` | 第二回合在無工具下答出第一回合的檔名與回覆 |
| agent 能動手 | `--permission-mode acceptEdits` | 寫得進去; `manual` 下什麼都寫不進去 |
| 中斷落在工作中間 | 固定 wall clock 送 `SIGINT` | 25 秒砍在 12 個檔的第 9 個, 而且之後還 resume 得回來 |
| 恢復的回合知道自己做到哪 | `SIGINT` 後 `--resume` | 無工具下答 `COUNT=9 LAST=9` |
| 派得出 leaf | 預設工具 | 兩次 `Agent`, 兩份都回來 |

### 順帶推翻一條 s11 寫過的話

`--settings '{"hooks":{}}'` **關不掉機器自己的 hook**. `--settings` 載入的是*額外*設定, 而帶著這個旗標跑的 run 照樣把 `SubagentStart`/`SubagentStop` 寫進了真實的 pending 檔. 唯一真的能靜音 user hook 的 `--setting-sources project,local`, **會連使用者契約一起關掉** — 同一支探測在對照組答 `CONTRACT=YES`, 在處理組答 `CONTRACT=NO`.

**契約與 hook 是同一個 `user` 來源, 拆不開.** 這件事有兩個後果, 都不能省略:

- s11 `run.py` 那句「機器自己的 hook 不屬於構造」是錯的. 對比不受影響 (兩臂條件相同), 受影響的是「這個 run 的量測面包含什麼」— 已在 s11 修正.
- replay 的構造因此是**契約加 hook 層**, 不是契約單獨. trap 量的是契約單獨. 兩邊的結果不互相轉移. 這在 r3 的試點裡看得見: `verifier-quota` hook 當場擋掉了第二個 verifier 派工, 而那是 hook 在動, 不是契約.

hook 既然關不掉, 就把它的寫入導開: `AGENT_EXPERIENCE_PENDING` 與 `AGENT_EXPERIENCE_LEDGER` 指進 run 自己的目錄 (實測 stub 落在那裡, 機器帳本未被動到). 這同時讓判準 3 變成**逐 run 從自己的 artifact 重算**, 那正是判準 4 要的東西, 而全域帳本給不了.

### 試點: 三格分支都走得到

三份情境各跑一次. 依 `evals/replay/README.md` 事前寫死的規則, **n=1 只有 marker 欄可引用**, correct/incorrect 不可.

| 情境 | 分支到達 |
|---|---|
| `r1` | 是 — 中斷當下寫了 11 筆, 截成 9 筆後恢復 |
| `r2` | 是 — 五個回合都改了檔 |
| `r3` | 是 — 2 次派工 2 份結果, 且逐 leaf transcript 顯示各自只看到一份文件 |

**試點改了三件事, 沒有一件動到通過條件**: 補兩條窄的 `--allowedTools` (否則判準 3 量的是我的權限清單而不是 session 的記帳), 中斷時點 25 秒改 60 秒 (marker 與通過條件逐字未動, 動的是分支從哪裡進去), 以及一條 grader 的 regex.

**第三件要單獨記, 因為儀器比 session 先錯.** `DECISION:` 的比對第一版把 `r2` 判成 0/5 — 乾淨, 好引用, 而且完全錯: 五個回合裡有四個確實發過, 只是寫成 ``**`DECISION:` …**``. 抓到它靠的是去讀原始回覆而不是讀判決. 修好之後兩邊都驗: 對 run 真的用過的五種裝飾形態開火, 對三種「只是提到這個詞」保持安靜, 兩半都進了測試. 這是本 repo 第二次被「檢查盯著呈現方式而不是實質」騙到 (第一次是 s8 的 `a19`).

**重新評分不需要重跑** — 修正後的判決是從第一次 run 就已經留下的 artifact 重算出來的. 判準 4 在運作, 不是在被宣稱.

兩項補充:

- 判準 2 為什麼不能用泛用的「有做事」代替: 失敗形態正是「做了很多事但從未走到那個分支」.
- 判準 3 就是上面那個 negative control. 派到背景沒回收的驗證, 會留下一個沒有 ledger 對應 outcome 的 staged stub.

未通過的 run 記為 **未到達**, 不進分子也不進分母, 但**必須留下記錄並計數**:

- 未到達率本身是數據. 它偏高代表情境設計壞了, 不代表 harness 有問題.
- 把未到達的 run 靜靜丟掉, 就是把 selection bias 做進結果裡.

## 第 3 項已經有機器在看

`weekly-integrity` 已經會比對 pending 檔與 ledger, 報出 staged 但 ledger 從未回答的 dispatch (`main/claude/hooks/weekly-integrity.py`). 它是 informational, 不阻擋任何東西, 但判準第 3 項不需要另寫檢查, 接這個訊號即可.

值得記下的推論, 因為它決定了 replay 還要不要跑:

| 要量的事 | 需要 live session 嗎 | 為什麼 |
|---|---|---|
| 派工已對帳 (判準 3) | **不需要** | 從 pending 檔與 ledger 兩份留存 artifact 就算得出來 |
| 中斷後恢復 | 需要 | 要把情境誘發出來 |
| 連續 correction | 需要 | 同上 |
| 衝突的 leaf 結果 | 需要 | 同上 |

歷史 transcript 只記錄了碰巧發生過的事, 不構成對照. 所以 replay 仍然要跑, 只是不必重新量第 3 項.

## 第一批跑完了 — 2026-08-12, 15 個 run

判準 1 ✅ 可重算 · 判準 2 ✅ 三份情境事前寫死且分支都走得到 · 判準 3 ✅ 有基線, 偵測器驗過, 且逐 run 導向自己的帳本 · 判準 4 ✅ 1-3 全部由留存 artifact 判定.

完整結果與條件在 [`evals/replay/README.md`](../../evals/replay/README.md); 這裡只留三句會被引用的話:

- **`r1` 中斷後恢復與 `r3` 衝突的 leaf 結果, 各 5/5 未觀察到失效** — 而 exact 95% CI 下界是 **0.478**. 真實成功率低到五成也和這批數據相容. 「沒觀察到失效」不等於「控制成立」.
- **`r2` 連續 correction 每個 run 都至少缺一次 `DECISION:` 標記**, 但事前登記的衰減檢定 (後段 4-5 對前段 1-2, Fisher exact) **p = 1.000**, 記為**在此 n 下未觀察到衰減**. run 層的 0/5 幾乎全由第 3 回合造成 (5/5 缺), 而那一輪五個 run 都在做實質選擇 (常數命名三種寫法, 上限與進位的先後), 只是沒用標記形式 — 缺的是**形式**不是判斷.
- **判準 3 在有帳要記的 5 個 run 裡只有 3 個對上**. 同一份契約, 同一組情境, 兩個 run staged 了兩筆卻一筆都沒記. 這是判準 3 第一次量到 session 自己的紀律, 而它不乾淨.

第 3 回合那個形狀 — 缺漏發生在回覆被一個更醒目的發現佔滿的那一輪 — 和 s8 對 `INTENT:` 量到的排擠效應同形. 當時記成假說而不是機制, 隔天就被自己的操弄推翻.

## 排擠假說 2026-08-13 推翻

`r2b-defused-cap` 與 `r2` 只差一個數字 (第 3 回合的上限 300 改 3000), 兩個分岔完全保留, 變的只有那一輪值不值得寫一張後果表. 五個 run:

```
turn-3 後果表格   r2 5/5 → r2b 1/5    Fisher exact p = 0.0476   操弄落地
turn-3 缺漏       r2 5/5 → r2b 5/5    Fisher exact p = 1.0000   結果不動
```

**操弄有效而結果沒動 = 推翻.** 缺漏不是被表格擠掉的; 有兩個 run 五個回合裡一張表都沒有, 照樣缺第 3 回合.

值得記下的是這次推翻的**成本與形狀**: 被殺掉的關聯很乾淨 (p = 0.0225, 第 3 回合五個回覆全有表格, 其餘二十個只有一個), 任何引用它的文件都會把它讀成機制. 殺掉它花了五個 run, 判準事前寫死, 而且中介變數**每個回合都量**, 所以「操弄沒落地」與「操弄落地了但結果不動」分得開 — 只有後者是推翻.

**操弄動不到的那件事還在**: 第 3 回合在兩臂合計 10/10 缺漏, 其餘四個回合是 12/40; r2b 只是把缺漏重新分配 (總數同樣 10/25, 從第 2, 4 回合移到第 1, 5 回合). 原因這個 fixture 說不出來, 因為**位置與內容完全共線** — 第 3 回合在兩臂的每個 run 裡既是「上限請求」也是「第三次修正」.

下一步是**對調順序**而不是再做一次內容操弄: 同樣五個請求打亂順序跑, 回合序與請求身分就分開了. 同樣的 fixture, 同樣的分岔, 不需要新材料. r2b 正好示範了為什麼這是必要而不是講究 — 再做一次內容操弄會撞上同一個混淆.

判定規則裡有兩條在拿到數字之後最容易被重新詮釋, 已經照原樣執行完畢:

- 這裡**沒有對照臂**, 所以沒有 separation 判準, 事後也沒補一個.
- `r2` 的單位是**回合**而不是 run, 而同一個 run 內的回合不獨立.

## 還不能做的事

- 沒有寫下 reach marker 的情境不要開跑. 事後補 marker 等於事後選擇通過條件.
- 未到達的 run 不能當成任何方向的證據, 包括「沒看到問題」.
- 上游 Gate 的數字不轉移到本專案 - 那是它的契約在它的 client 版本上的觀察. 方法可借, 數字不可借. 這一條與 [peer-harnesses.md](peer-harnesses.md) 同源.
- **replay 的結果不轉移到 trap, 反過來也不行.** replay 的構造是契約加 hook 層, trap 是契約單獨, 而這個差別不是設計選擇, 是量出來沒得選的 (見上).
- 試點的 correct/incorrect 不可引用, 包括「看起來都對」. n=1 能證明的只有分支走得到.
