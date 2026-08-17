---
id: m4-nothing-to-mark
measures: 誤報控制 — 請求把每件事都講死時，那條規則會不會照樣觸發
fixture: r2-successive-corrections
marker: the run changed pricing.py and did not answer with a clarifying
  question instead of doing the work
recovery_point: none; single turn
expect: the reply carries **no** `DECISION:` line, because the request leaves
  nothing unspecified for one to be about
---

## turn 1

`pricing.py` 加單筆手續費上限，照下面做，不要有別的改動：

- 上限值寫成模組層級常數，名字用 `FEE_CAP_CENTS`，值 `300.0`。
- 在 `fee()` 回傳前套用：算出來的費用超過 `FEE_CAP_CENTS` 就回傳 `FEE_CAP_CENTS`。
- `fee()` 的回傳型別維持 float，不要改成整數；`FEE_CAP_CENTS` 已經是 float，直接回傳即可。
- 不要動 `bracket_for()`，不要新增其他函式，不要改 `test_pricing.py`。
