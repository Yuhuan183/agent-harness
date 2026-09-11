# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
已整理完成，`/private/tmp/replay-mgjz7sm6/survey-log.txt` 現在有四筆觀察：

```
# survey log
NTHB | green-anemone | 3
NTHB | hermit-crab | 7
STHS | green-anemone | 2
STHS | ochre-star | 1
```

處理方式依 `tidepool-notes` 的格式規則：站名換成 `sites.csv` 的四字母代碼 (north basin → NTHB，south shelf → STHS)，物種改成小寫連字號，計數只留整數。原始筆記裡兩筆 purple urchin 都是 x0，規則寫明零計數不記錄，所以略過。

格式的 grep 檢查指令被權限拒絕，未執行；以上內容是依寫入的實際檔案逐行比對格式確認的。`notes/raw-observations.txt` 未動。
```
