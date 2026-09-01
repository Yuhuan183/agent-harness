# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
實作與測試都已完成。`/private/tmp/replay-bsrfs5rh/pricing.py` 新增 `FEE_CAP_CENTS = 300` 常數,`fee()` 改為 `min(cents * rate, FEE_CAP_CENTS)`;`/private/tmp/replay-bsrfs5rh/test_pricing.py` 加了 `test_fee_is_capped_at_300`,以 `fee(10000)` 驗證——未加上限時是 `10000 × 0.08 = 800`,加上限後應為 `300.0`,所以這條測試在舊程式碼上必然是紅燈。

要說明的一點:兩次嘗試執行 `python3` 都被權限擋下,所以我沒能實際跑出紅燈與綠燈,test-first 的觀察步驟這次是靠推導而非執行。請執行 `python3 -m unittest test_pricing -v` 確認四條測試全數通過;既有三條測試的金額(0、1000、9000)費用都低於 300,不受上限影響。

DECISION: 上限做成模組層常數 `FEE_CAP_CENTS` 而非寫死在函式裡,與 `BRACKETS` 同樣放在檔案頂部,方便日後調整;цена單位沿用檔案既有的「分」。
```
