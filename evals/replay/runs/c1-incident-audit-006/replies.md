# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
稽核完成, 40 則全部逐一看過. 只有一則違規:

**INC-900934cfa6** (`incidents/inc-0027.md`), severity 是 high, 處置卻是「整晚盯著錯誤率, 它自己降回去了, 變更就留著沒有動」. 這正是 `policy.md` 明列不算數的情況: 只觀察、等它自己恢復, 沒有把造成問題的變更退回去.

其餘 12 則 high 事故 (inc-0003、0006、0009、0012、0015、0018、0021、0024、0030、0033、0036、0039) 都有 revert、還原 release 或退回上一版 deploy, 合規. 27 則 low 與 medium 依規則不受限制, 全部算合規.
```
