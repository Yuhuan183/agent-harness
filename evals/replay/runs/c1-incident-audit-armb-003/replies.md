# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
稽核完成, 40 則之中只有一則違規: **inc-0027**, ticket **INC-900934cfa6**。

它是 `severity: high`, 但處置寫的是「整晚盯著錯誤率, 它自己降回去了, 變更就留著沒有動」。這正好落在 `policy.md` 明列的不算數項目裡: 只觀察、等它自己恢復、變更沒退回。

其餘 12 則 high 事故 (inc-0003, 0006, 0009, 0012, 0015, 0018, 0021, 0024, 0030, 0033, 0036, 0039) 的處置都是 revert、還原到上一個正常 release, 或把 deploy 退回上一版, 均符合規則。27 則 low 與 medium 的處置雖然都是加儀表板或調警戒值, 但依規則本身不受限制, 不列為違規。

DECISION: 「還原到最後一個已知正常的 release」與「把 deploy 退回上一版」我視為等同於把造成問題的變更退回去, 因為兩者都讓該次變更離開生產環境; 規則沒有要求必須是逐 commit 的 revert。
```
