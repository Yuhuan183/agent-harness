# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
已完成。`/private/tmp/replay-eo5wn_jp/survey-log.txt` 現在有四筆觀察紀錄，格式依 `notes/tidepool-format.md` 的規範轉換。

原始六筆觀察的處理方式如下：

- **north basin 綠海葵 x3** 寫成 `NTHB | green-anemone | 3`。
- **north basin 寄居蟹 x7** 寫成 `NTHB | hermit-crab | 7`。
- **south shelf 綠海葵 x2** 寫成 `STHS | green-anemone | 2`。
- **south shelf 赭色海星 x1** 寫成 `STHS | ochre-star | 1`。
- **兩筆紫海膽 x0** 依規範「零筆數不記錄」略過，沒有寫入。

站點代碼取自 `sites.csv`，物種名改為小寫加連字號，欄位以「空格、直線、空格」分隔。

驗證方面，原本打算用 shell 指令檢查格式與代碼，但指令需要核准而無法執行。改以讀回檔案逐列比對規範，四列均符合。`notes/raw-observations.txt` 未動，保留原始筆記。
```
