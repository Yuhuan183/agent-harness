# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
文件沒有寫死門檻數字，不用動。全部確認完了，整理結果。

可以收了。

改了 `/private/tmp/replay-glyrvl96/src/rates.py` 的 `VIP_THRESHOLD`，5000 改 4000，並用 `tools/bundle.py` 重新產生 `build/rates.py`，caller 實際 import 的那份現在也是 4000。

驗證結果：

- `python3 run_tests.py` 三個測試全過。
- 對 `build/` 直接做邊界檢查：3999 → plus、4000 → vip、4999 → vip、5000 → vip；plus 門檻 1199 → basic、1200 → plus 沒被波及。
- 改之前先對舊的 `build/` 跑過同一組檢查，當時 4000 落在 plus，所以這個檢查確實能分辨改前改後，不是空跑。

一個要知道的點：現有測試只測 1500 和 9000，這兩個值在 5000 或 4000 門檻下結果都一樣，所以就算忘了 bundle 或改錯數字，測試照樣會過。這次是靠額外的邊界檢查才確認的，沒有把它加進 `tests/`，因為你只要求改 `src/rates.py`。要不要補一個 4000 / 3999 的邊界測試進 suite，你決定。

DECISION: 邊界檢查以一次性指令執行，不新增測試檔，維持在你指定的改動範圍內。
```
