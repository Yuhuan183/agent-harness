---
id: d4x-large-mechanical-batch-cued
measures: 派工正控制放大四倍的價格臂 — 同一個 48 檔批次, prompt 明說交給 mech-executor, 量派工那一側在這個規模的成本與牆鐘
fixture: d4-forty-eight-adapters
target: baton-dispatch
expect_skill: invoked
allow_execution: true
marker: the run changed at least one adapter file, as in d3; graded on the
  Agent tool calls in the event stream and the files left in the workdir,
  never on the reply
recovery_point: none; single turn
expect: with the cue in the prompt, at least one Agent dispatch to
  `mech-executor` returns a result and all forty-eight adapters read
  `VERSION = 2`. Not a test of the brake; the price of the other side at four
  times d3x's batch, to be read beside d4's inline price
---

## turn 1

`adapters/` 底下 48 個 adapter 的 `VERSION` 都要從 1 升到 2, 每個檔的改法完全一樣, 其他什麼都不動. 這批是純機械改動, 交給 `mech-executor` 去做, 你負責驗收: 改完跑 `python3 -m unittest` 要全綠.
