# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
完成了。`pricing.py` 的 `fee()` 現在會以 `FEE_CAP_CENTS = 300` 封頂,並同步在 `test_pricing.py` 加了 `test_fee_capped_at_300`(金額 10000 分落在 8% 級距,未封頂手續費 800 分,斷言封頂後為 300)。

有一件事要如實說明:這個環境的 Bash 權限擋下了 `find`、`python3 -m unittest`、`python3 test_pricing.py`,所以我沒能實際看到新測試先紅後綠——test-first 的 gate 是靠推算補的,不是靠執行。斷言的預期值(300)來自獨立的手算,對修改前的程式碼(會回傳 800.0)必然失敗,對修改後必然通過;既有三個測試的行為也不受影響(0、50、級距判定都在封頂之下)。請在你的終端跑一次 `python3 -m unittest test_pricing` 確認四個測試全綠。

另外補一點邊界說明:目前三個級距的最高「未封頂」手續費在中間級距是 250 分(5000 分 × 5%),所以封頂只會對最高級距(> 5000 分)生效,那個級距從 5001 分起手續費就已超過 300 分,等於整段都取 300。
```
