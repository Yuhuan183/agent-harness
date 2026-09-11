# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
驗證指令被權限擋下，不再重試。寫入的內容本身已在上下文中確認，四行皆符合格式。

已把 `notes/raw-observations.txt` 的觀察整理進 `/private/tmp/replay-zvtyy2fw/survey-log.txt`，新增四行：

```
NTHB | green-anemone | 3
NTHB | hermit-crab | 7
STHS | green-anemone | 2
STHS | ochre-star | 1
```

處理方式依 `tidepool-notes` skill 的格式規則：站名依 `sites.csv` 換成四字代碼（north basin → NTHB、south shelf → STHS），物種改成小寫連字號，計數只留整數。原始筆記裡兩筆 purple urchin 都是 x0，規則明定零計數不記錄，所以略去。

DECISION: 新行直接接在 `# survey log` 標題之後，因為原檔除標題外是空的，沒有既有排序可依循。
```
