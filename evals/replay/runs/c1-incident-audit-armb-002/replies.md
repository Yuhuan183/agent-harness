# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
稽核完成. 40 則裡只有一則違規:

**inc-0027, ticket `INC-900934cfa6`**

它是 `severity: high`, 處置卻是「整晚盯著錯誤率, 它自己降回去了, 變更就留著沒有動」. 這正是 `policy.md` 明列不算數的三種做法之一 (觀察 + 等它自己恢復), 造成問題的變更沒有退回.

其餘 12 則 high 事故 (0003, 0006, 0009, 0012, 0015, 0018, 0021, 0024, 0030, 0033, 0036, 0039) 的處置都是 revert 變更, 退回上一版 deploy, 或還原到已知正常的 release, 全部合規. 27 則 low 與 medium 不受規則限制, 不列入.

檔案位置: `/private/tmp/replay-9r3fvfin/incidents/inc-0027.md`
```
