# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
已完成。`/private/tmp/replay-gyae_ird/survey-log.txt` 現在內容如下：

```
# survey log
NTHB | green-anemone | 3
NTHB | hermit-crab | 7
STHS | green-anemone | 2
STHS | ochre-star | 1
```

處理方式：

- **站點代碼**：north basin → `NTHB`、south shelf → `STHS`，依 `sites.csv` 對照。
- **物種名稱**：轉小寫並以連字號取代空格。
- **略過的兩筆**：north basin 與 south shelf 的 purple urchin 都是 x0，依格式規則不寫入。

原始檔 `notes/raw-observations.txt` 未動。
```
