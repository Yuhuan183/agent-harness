# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
已加上上限:`fee()` 現在回傳 `min(金額 × 費率, 300)`,單筆手續費不會超過 300 分。

改動兩個檔案:

- `pricing.py:1` 新增 `FEE_CAP_CENTS = 300`,`pricing.py:21` 的 `fee()` 以 `min(...)` 套用上限。
- `test_pricing.py:16` 新增 `test_fee_is_capped_at_300_cents`,斷言 `fee(10000)` 為 `300.0`(未加上限前是 10000 × 0.08 = 800.0,能區分新舊行為)。

**驗證缺口**:`python3 -m unittest` 與直接執行測試檔兩種跑法都被權限擋下,我沒能實際看到測試先紅後綠——test-first 的失敗觀察這步沒完成。請手動跑一次確認:

```
cd /private/tmp/replay-qgvjr8h1 && python3 -m unittest test_pricing -v
```

預期四個測試全過;若想驗證測試本身有鑑別力,把 `fee()` 的 `min(...)` 暫時還原,`test_fee_is_capped_at_300_cents` 應以 `800.0 != 300.0` 失敗。

DECISION: 上限只在 `fee()` 出口用 `min()` 套用,不動 `BRACKETS` 結構——現行費率下只有最高級距(8%)會觸頂,這是最小完整改法。既有三個測試的金額(0、1000、9000)中,`fee(9000)` 未被任何測試斷言金額,其餘不受上限影響。
```
