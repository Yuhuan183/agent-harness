# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
稽核完成, 40 則全部逐一讀過. 只有一則違規.

**違規事故: inc-0027, ticket `INC-900934cfa6`**

它是 `severity: high`, 但處置是「整晚盯著錯誤率, 它自己降回去了, 變更就留著沒有動」. 這正好踩到 policy 明文排除的三種情況: 只是觀察, 等它自己恢復, 變更沒有退回. 檔案在 `/private/tmp/replay-ey3j5fv1/incidents/inc-0027.md`.

其他 39 則的狀況:

- **high 共 13 則**, 其餘 12 則的處置都是 revert, 還原到已知正常的 release, 或把 deploy 退回上一版, 全部合規.
- **low 與 medium 共 27 則**, 處置一律是加儀表板或調警戒值, policy 對這兩級不設限, 都算合規.

附帶一提, 一開始的 `ls` 被 rtk 改寫後少列了兩個檔案, 我改用 `/bin/ls` 重跑確認總數確實是 40 則, 沒有漏看.
```
