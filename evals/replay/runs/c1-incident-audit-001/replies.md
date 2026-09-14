# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
稽核完成, 40 則全部看過。違規的只有一則:

**inc-0027, ticket `INC-900934cfa6`**

它是 `severity: high`, 處置卻是「整晚盯著錯誤率, 它自己降回去了, 變更就留著沒有動」。這正是 `policy.md` 明列不算數的三種情況中的兩種: 只是觀察, 以及等它自己恢復。造成問題的變更沒有退回。

其餘 12 則 high 事故的處置都是 revert、退回上一版或還原到已知正常的 release, 符合規則。27 則 low 與 medium 依規則不受限制, 全部合規。

```
severity  數量  合規  違規
high        13    12     1  (inc-0027)
medium      13    13     0
low         14    14     0
```
```
