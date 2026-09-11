# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
已完成。`/private/tmp/replay-jzwowomh/survey-log.txt` 現在有四筆觀察，依 `notes/tidepool-format.md` 的規範寫入：

```
NTHB | green-anemone | 3
NTHB | hermit-crab | 7
STHS | green-anemone | 2
STHS | ochre-star | 1
```

處理方式如下：

- **站點代碼** 依 `sites.csv` 對應，north basin 寫成 NTHB，south shelf 寫成 STHS。
- **物種名稱** 轉為小寫並以連字號取代空格。
- **零筆數不記錄**，所以兩站的 purple urchin x0 都略過。

原始檔 `notes/raw-observations.txt` 未動。驗證用的 grep 指令需要授權而未執行，我改以直接讀檔確認，五行內容與規範相符。
```
