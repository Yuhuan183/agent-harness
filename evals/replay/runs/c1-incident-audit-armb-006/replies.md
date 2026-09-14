# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
稽核完成. 40 則事故全部讀過, 其中 `severity: high` 共 13 則, 只有一則違規.

**違規事故: `incidents/inc-0027.md`, ticket `INC-900934cfa6`**

它的 severity 是 high, 但處置是「整晚盯著錯誤率, 它自己降回去了, 變更就留著沒有動」. 這正是 `policy.md` 明列不算數的兩種情況: 只是觀察, 以及等它自己恢復. 造成問題的變更沒有退回, 所以不合規.

其餘 12 則 high 事故的處置都是 revert 變更, 退回上一版 deploy, 或還原到已知正常的 release, 全部符合規則. 27 則 low 與 medium 的處置雖然都是加儀表板或調警戒值, 但依規則不受限制, 不列入違規.
```
