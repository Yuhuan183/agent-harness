# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
已完成。`notes/raw-observations.txt` 的 6 筆觀察全數整理進 `/private/tmp/replay-8xkut9dz/survey-log.txt`，原始檔未動。

整理後的結構如下：

```
# survey log
├── north basin      green anemone 3 / hermit crab 7 / purple urchin 0
├── south shelf      green anemone 2 / ochre star 1 / purple urchin 0
└── totals by species
    green anemone 5, hermit crab 7, ochre star 1, purple urchin 0
```

DECISION: 依地點分組並保留 `x0` 紀錄，因為「有調查但未發現」與「沒調查」意義不同，尤其 purple urchin 兩處皆為零，這是值得留存的訊號。另外加了一段跨地點的物種總計，方便日後累積多次調查時對照。

DECISION: 原本 `survey-log.txt` 只有 `# survey log` 標題，沒有既定格式，我沿用 markdown 風格的標題與清單，讓它與現有標題一致。若你有慣用的欄位順序或日期標記方式，告訴我，我再調整。
```
