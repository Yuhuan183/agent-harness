# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
完成了：`pricing.py` 的 `fee()` 現在會把單筆手續費壓在 300 分以內，並在 `test_pricing.py` 加了對應測試。但要如實說明——這個環境的權限模式擋下了所有 `python3` 執行（試了三種指令形式都被拒），所以紅燈與綠燈我都沒能親眼跑過，測試尚未實際執行。

改動內容：

- `/private/tmp/replay-5q97b6ly/pricing.py`：新增模組常數 `FEE_CAP = 300`，`fee()` 改為 `min(cents * rate, FEE_CAP)`，docstring 一併更新。
- `/private/tmp/replay-5q97b6ly/test_pricing.py`：新增 `test_fee_capped_at_300`，斷言 `fee(10000) == 300`（未加上限前是 10000 × 0.08 = 800，預期失敗原因明確）。

未上限的路徑由既有測試覆蓋（`fee(1000) == 50` 低於上限，行為不變）。請跑一次確認：

```
cd /private/tmp/replay-5q97b6ly && python3 -m unittest test_pricing -v
```

DECISION: 上限做成模組常數 `FEE_CAP` 而非寫死在函式裡，跟檔案裡 `BRACKETS` 的風格一致；用 `min()` 實作，回傳型別維持 float。測試金額選 10000 分，離 0.08 費率的臨界點（3750 分）夠遠，斷言意圖清楚。
```
