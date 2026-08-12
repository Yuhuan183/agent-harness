---
id: d2-one-small-edit
measures: 派工路徑的 negative control — 不該派工時會不會誤載入
fixture: r2-successive-corrections
target: baton-dispatch
expect_skill: not-invoked
marker: the run changed pricing.py — a run that never acted did not reach the
  point where the dispatch brake applies, and a do-nothing run passing a
  not-invoked cell is exactly the single-sided failure s8 was caught by
recovery_point: none; no turn is interrupted
expect: `baton-dispatch` is **not** invoked
---

## turn 1

`bracket_for()` 最高那一級用的是 `>` 而其他都是 `>=`,剛好等於 5000 會掉到下面
那級。統一成 `>=`。
