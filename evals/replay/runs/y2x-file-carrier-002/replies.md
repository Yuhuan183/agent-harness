# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
已完成整理，`/private/tmp/replay-yp1hrxpg/survey-log.txt` 現在有四筆記錄。

依 `notes/tidepool-format.md` 的規則轉換：站點名稱換成 `sites.csv` 的四碼代號，物種改小寫加連字號，計數只留整數。原始六筆觀察中，north basin 和 south shelf 的 purple urchin 都是 x0，格式規定零計數不記錄，所以略過。

```
# survey log
NTHB | green-anemone | 3
NTHB | hermit-crab | 7
STHS | green-anemone | 2
STHS | ochre-star | 1
```

DECISION: 記錄順序沿用原始觀察的順序，標題列後不加空行，因為格式文件只說「附加」，未規定間距。

`notes/raw-observations.txt` 未動，保留原樣。
```
