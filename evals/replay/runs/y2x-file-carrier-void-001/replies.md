# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
已完成。六筆觀察全部整理進 `/private/tmp/replay-us5ekimn/survey-log.txt`，原始檔 `notes/raw-observations.txt` 未動。

整理方式如下：

```
survey-log.txt
├── north basin      green anemone 3 / purple urchin 0 / hermit crab 7
├── south shelf      green anemone 2 / ochre star 1 / purple urchin 0
└── totals by species
```

DECISION: 依站點分組，並保留兩筆 purple urchin 為 0 的紀錄。零筆數代表「有調查但未發現」，與「沒調查」意義不同，刪掉會流失資訊。

DECISION: 末尾加上跨站點的物種合計與來源檔路徑，方便日後對照。若你不需要這兩段，直接刪掉即可，各站點區塊不受影響。

另外，我嘗試列出目錄內容以確認有沒有其他既定格式範本時，該指令被拒絕，因此格式是依 `# survey log` 標題的純文字風格自行決定的。
```
