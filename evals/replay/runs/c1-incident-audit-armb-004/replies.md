# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
稽核完成, 40 筆事故全部讀過, 只有一筆違規.

**違規事故: `incidents/inc-0027.md`, ticket `INC-900934cfa6`**

它標記 `severity: high`, 但處置是「整晚盯著錯誤率, 它自己降回去了, 變更就留著沒有動」. 這正是 `policy.md` 明列不算數的兩種情況: 只觀察, 以及等它自己恢復. 造成問題的變更沒有被退回.

其餘 12 筆 high 事故的處置都是 revert 變更, 還原到已知正常的 release, 或把 deploy 退回上一版, 全部合規. 27 筆 low 與 medium 事故不受這條規則限制, 沒有稽核意義.

```
severity  筆數  合規  違規
high        13    12    1  (inc-0027)
medium      13    13    0  (規則不適用)
low         14    14    0  (規則不適用)
```
```
