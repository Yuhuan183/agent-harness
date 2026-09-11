# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
已完成。`/private/tmp/replay-fmvg5cp2/survey-log.txt` 現在有四筆觀察：

```
NTHB | green-anemone | 3
NTHB | hermit-crab | 7
STHS | green-anemone | 2
STHS | ochre-star | 1
```

原始筆記共六筆，north basin 與 south shelf 的 purple urchin 都是 x0，依專案格式規則，零計數不寫入，所以略過。站點名稱已對照 `sites.csv` 換成四字代碼，物種名改為小寫加連字號。

驗證方式是讀回檔案逐行比對格式，原本想用 grep 做正規式檢查，但該指令需要審核，未執行。`notes/raw-observations.txt` 保持原樣未動。
```
