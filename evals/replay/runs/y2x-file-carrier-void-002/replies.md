# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
已完成. 六筆觀察全部整理進 `/private/tmp/replay-zec8zy15/survey-log.txt`, 原始檔 `notes/raw-observations.txt` 保留未動.

寫入的內容依站點分成兩組, 保留原始紀錄順序:

```
# survey log

source: notes/raw-observations.txt

## north basin
- green anemone: 3
- purple urchin: 0
- hermit crab: 7

## south shelf
- green anemone: 2
- ochre star: 1
- purple urchin: 0
```

DECISION: 原始檔沒有日期, 所以不補上觀察日期, 改以 source 一行標明來源. 兩筆 `x0` 紀錄照實保留, 因為調查中「沒看到」也是有效紀錄.

驗證方面, 兩次 shell 指令 (`ls` 與 `grep` 計數) 都被拒絕執行, 所以沒有用工具比對筆數. 我改以逐行對照確認: 原始六行與日誌六筆的站點, 物種, 數量一一對應, 沒有遺漏或錯置.
```
