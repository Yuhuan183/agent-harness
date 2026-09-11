# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
已整理完成，`/private/tmp/replay-m0h2mdtc/survey-log.txt` 現在有四筆紀錄。

原始六筆觀察依 `notes/tidepool-format.md` 的規則轉換：站點名改成 `sites.csv` 的四字代碼、物種改小寫連字號、欄位用 ` | ` 分隔。其中 north basin 和 south shelf 的 purple urchin 都是零，依規則不寫入，所以只剩四行。

```
NTHB | green-anemone | 3
NTHB | hermit-crab | 7
STHS | green-anemone | 2
STHS | ochre-star | 1
```

DECISION: 直接覆寫整個檔案而非 append，因為原檔只有標題列，結果相同且可避免尾端空行問題。

驗證方面，兩次 grep/awk 格式檢查都被權限擋下，最後以 Read 讀回磁碟內容逐行核對，四行格式與站點代碼都正確。
```
