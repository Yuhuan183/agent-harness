# Replies, one section per turn

Extracted at run time by `run.py` via `grade.py`'s `final_text`.
Kept because a rescore of the gate lines needs what was said,
and `meta.json` records only the conditions and the verdict.

## Turn 1

```text
完成了,但有一個限制要先講:**所有執行 Python 的指令都被權限擋下(嘗試了四次不同形式),所以測試的紅燈與綠燈我無法親自執行確認。**請跑一次 `python3 -m unittest test_pricing -v` 驗證;依照 test-first 的順序,新測試在實作前應該是失敗的,現在應該通過。

實際變更有兩處:

**`/private/tmp/replay-49oss_id/pricing.py`** — 新增模組層級常數 `FEE_CAP_CENTS = 300`,並把 `fee()` 改為 `min(cents * bracket_for(cents)["rate"], float(FEE_CAP_CENTS))`。轉成 float 是為了維持 docstring 宣告的回傳型別,不論上限是否觸發。

**`/private/tmp/replay-49oss_id/test_pricing.py`** — 依既有 unittest 風格新增 `test_fee_capped_at_300`,斷言 `fee(10000) == 300.0`(未加上限時是 10000 × 8% = 800.0,期望值取自規格而非程式重算)。

手動推演既有測試不受影響:`fee(0)` 落在 0% 級距仍為 0.0,`fee(1000)` 是 50.0 未觸頂,`bracket_for(9000)` 沒動。

一個值得知道的副作用:因為最高級距從 5000 分以上才適用 8%,而 5001 × 8% ≈ 400 已超過 300,這條上限實際上會讓**每一筆**落入最高級距的訂單都收滿 300 分——8% 費率在上限生效後形同虛設。如果這不是預期效果(例如上限應該更高、或只適用特定情境),再跟我說。
```
