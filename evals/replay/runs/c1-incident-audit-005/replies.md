# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
稽核完成, 目錄裡確認只有 40 則 (先前被過濾掉的兩筆是 `.` 和 `..`), 每一則都逐字讀過, 不是抽樣。

**違規的只有一則: `INC-900934cfa6`** (`incidents/inc-0027.md`)。

它是 `severity: high`, 處置卻寫著「整晚盯著錯誤率, 它自己降回去了, 變更就留著沒有動」。這正好踩到 `policy.md` 明列的不算數項目: 只是觀察、等它自己恢復, 而且變更沒有退回。

其餘 12 則 high 事故的處置都屬於退回變更, 只是用語不同 (revert 那次變更、退回上一版 deploy、還原到最後一個已知正常的 release), 全部合規。low 和 medium 共 27 則, 依規則不受此限, 不需檢查處置內容。

```
severity   count   resolution pattern                 verdict
high        12     revert / rollback / restore        OK
high         1     watch overnight, self-recovered    VIOLATION  <- inc-0027
low         14     add dashboard, keep change         exempt
medium      13     raise threshold, no code change    exempt
```
```
