# lifecycle replay: 存活判準

狀態: **只有判準, replay 尚未開跑**. 這是刻意的順序, 不是進度落後.

lifecycle replay 想量的三件事 — 中斷後恢復、連續 correction、互相衝突的 leaf 結果 — 目前都
沒有本機實證, 這一點記在 [研究摘要](README.md) 的驗證缺口. 本文只解決前置問題: 一次 replay
的結果要滿足什麼條件才有資格被引用.

## 為什麼判準要先寫

replay 量的絕大部分是「沒發生」: 中斷後沒有重複寫入、correction 沒有失控疊加、衝突的 leaf
結果沒有被靜靜吞掉. 「沒發生」是最容易假造的一種數據 —— 一個什麼都沒做的 session, 在每一
個「沒發生」欄位上都是滿分.

這種數據的問題不在於錯, 而在於**難以撤回**. 一旦寫進文件, 後續引用者看到的是「已驗證」,
看不出它底下是空的. 先跑再補判準, 等於先製造一批要靠人記得去質疑的結論.

上游提供了現成的 negative control: 它記錄過一次「把驗證派到背景後從未回收」. 那一輪在所有
「沒發生」的欄位上都乾淨, 因為根本沒有東西發生. **存活判準連這個案例都抓不到, 就不要開跑.**

## 判準

一次 replay run 的「沒發生」要算數, 四項全過:

1. **活著結束**: session 跑到自然結束, 不是 context 耗盡、crash 或人為中斷 (被測的中斷情境
   除外, 那種中斷本身是受測條件, 要在情境裡寫明預期的恢復點).
2. **到達受測邊界**: 每個情境必須事先寫下一個 **reach marker** —— 一個只有在 session 真的
   走到被測分支時才會存在的具體 artifact (某個 commit、某份 leaf 報告、某條 ledger 記錄).
   泛用的「有做事」不夠: 失敗形態正是「做了很多事但從未走到那個分支」.
3. **派工已對帳**: 這個 session staged 的每一筆 dispatch, 在 ledger 都要有對應 outcome.
   這一項就是上面那個 negative control —— 派到背景沒回收的驗證, 會留下一個沒有 ledger 對應
   的 staged stub.
4. **可獨立重算**: 前三項的檢查, 必須由沒有跑過該 session 的人從留存 artifact 重算得出.
   跑的人自己說「有到達」不算證據.

未通過的 run 記為 **未到達**, 不進分子也不進分母, 但**必須留下記錄並計數**. 未到達率本身是
數據: 它偏高代表情境設計壞了, 不代表 harness 有問題. 把未到達的 run 靜靜丟掉, 就是把
selection bias 做進結果裡.

## 第 3 項已經有機器在看

`weekly-integrity` 已經會比對 pending 檔與 ledger, 報出 staged 但 ledger 從未回答的 dispatch
(`main/claude/hooks/weekly-integrity.py`). 它是 informational, 不阻擋任何東西, 但判準第 3 項
不需要另寫檢查, 接這個訊號即可.

值得記下的推論: **這一項生命週期事實不需要 live session 就量得到** —— 它從 pending 檔與
ledger 兩份留存 artifact 算得出來. 但另外三件事 (中斷恢復、連續 correction、衝突結果) 需要
把情境誘發出來, 歷史 transcript 只記錄了碰巧發生過的事, 不構成對照. 所以 replay 仍然要跑,
只是不必重新量第 3 項.

## 還不能做的事

- 沒有寫下 reach marker 的情境不要開跑. 事後補 marker 等於事後選擇通過條件.
- 未到達的 run 不能當成任何方向的證據, 包括「沒看到問題」.
- 上游 Gate 的數字不轉移到本專案 —— 那是它的契約在它的 client 版本上的觀察. 方法可借,
  數字不可借. 這一條與 [peer-harnesses.md](peer-harnesses.md) 同源.
