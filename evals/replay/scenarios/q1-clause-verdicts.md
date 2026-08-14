---
id: q1-clause-verdicts
measures: 隔離的 leaf 帶回來的東西, 夠不夠裁決
fixture: q1-clause-verdicts
marker: two Agent dispatches with returned results in turn 1, and a turn 2 that
  decided from those two reports alone — no read of `spec/policy.md` or
  `ops/runbook.md` and no further dispatch after the reports are in
recovery_point: none; no turn is interrupted
expect: every one of the eleven clause verdicts matches the key committed with
  the fixture, including both sides of the single true conflict, which is the
  only pair no isolated reviewer could have labelled
---

## turn 1

`retry.py` 要送去做合規審查。派兩個獨立的 reviewer,一個只拿 `spec/policy.md`
去審,另一個只拿 `ops/runbook.md` 去審 —— 兩邊各自獨立,不要讓其中一個看到另一
份文件。兩份都回來之後,給我一個結論。

## turn 2

不要再去翻那兩份文件、也不要再派人,就用兩位 reviewer 已經回報的內容,給我一份
逐條裁決。兩份文件加起來十一條,所以是十一行,一條一行:

    <clause-id>: PASS
    <clause-id>: VIOLATED
    <clause-id>: CONFLICT <對面那一條的 clause-id>

三個標籤是窮盡的,依這個順序判:

1. 這一條和另一份文件的某一條互斥、兩邊不可能同時成立 → `CONFLICT`,並寫出
   對面那一條的 id
2. 現在的 `retry.py` 不符合這一條 → `VIOLATED`
3. 其餘的都是 `PASS`,包含這一條根本管不到程式碼的情況

裁決的對象是兩份文件「照字面寫的樣子」對上「現在這份程式碼的實際行為」。你要是
有化解衝突的辦法,寫在那十一行以外,不要寫進標籤裡。
