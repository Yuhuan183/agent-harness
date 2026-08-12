# lifecycle replay: 存活判準

狀態: **只有判準, replay 尚未開跑**. 這是刻意的順序, 不是進度落後.

lifecycle replay 想量的三件事 - 中斷後恢復, 連續 correction, 互相衝突的 leaf 結果 - 目前都沒有本機實證, 這一點記在 [研究摘要](README.md) 的驗證缺口. 本文只解決前置問題: 一次 replay 的結果要滿足什麼條件才有資格被引用.

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

`evals/scripts/lifecycle-criteria.py` 把判準 1 與 3 做成一道命令, 永遠 exit 0. 判準 2 不放進去: reach marker 依定義是逐情境的, 而 `evals/traps/*/grade.py` 已經在從 event stream 重算它.

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

現在剩 12 筆, 全部不屬於本輪工作. 判準 3 有乾淨基線了.

## 還缺什麼才能開跑

判準 1 ✅ 可重算 · 判準 3 ✅ 有基線且偵測器驗過 · 判準 4 ✅ 只要 1-3 是 artifact 判定就成立.

**只剩判準 2**: replay 需要一份**事前寫好 reach marker 的情境**. 機制是現成的 (s11 的 `marker_pattern` 與 s10/s11 的 grader), 缺的是針對「中斷後恢復 / 連續 correction / 衝突的 leaf 結果」這三件事各寫一份情境, 並在跑之前寫下各自的恢復點與 marker.

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

## 還不能做的事

- 沒有寫下 reach marker 的情境不要開跑. 事後補 marker 等於事後選擇通過條件.
- 未到達的 run 不能當成任何方向的證據, 包括「沒看到問題」.
- 上游 Gate 的數字不轉移到本專案 - 那是它的契約在它的 client 版本上的觀察. 方法可借, 數字不可借. 這一條與 [peer-harnesses.md](peer-harnesses.md) 同源.
