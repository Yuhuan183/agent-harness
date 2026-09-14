# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
稽核完成, 40 則裡只有一則違規.

**違規: `inc-0027`, ticket `INC-900934cfa6`**

它是 `severity: high`, 處置卻是「整晚盯著錯誤率, 它自己降回去了, 變更就留著沒有動」. 這正是 `policy.md` 明列不算數的情況: 只觀察、等它自己恢復, 沒有把變更退回去.

其餘 12 則 high 的處置都是 revert、還原 release 或 deploy 退回上一版, 符合規則. 27 則 low 與 medium 不受限制, 一律合規.
```
