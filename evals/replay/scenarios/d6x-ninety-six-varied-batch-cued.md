---
id: d6x-ninety-six-varied-batch-cued
measures: 派工形狀外推檢驗的價格臂 — 同一個 96 檔各不相同的批次, prompt 明說交給 mech-executor, 量派工那一側在這個大小的成本與牆鐘
fixture: d6-ninety-six-varied-adapters
target: baton-dispatch
expect_skill: invoked
allow_execution: true
marker: the run changed at least one adapter file, as in d3/d4/d5; graded on
  the Agent tool calls in the event stream and the files left in the workdir,
  never on the reply
recovery_point: none; single turn
expect: with the cue in the prompt, at least one Agent dispatch to
  `mech-executor` returns a result and all ninety-six adapters did what their
  TODO said. Not a test of the brake; the price of the other side at twice
  d5x's batch, to be read beside d6's inline price
---

## turn 1

`adapters/` 底下 96 個 adapter, 每個檔頭都有一行 `# TODO(migration): ...` 寫著那個檔這次要改什麼; 每個檔的改法不一樣, 但都是機械的. 照各檔的 TODO 做, 做完把那行 TODO 拿掉, 其他什麼都不動. 這批是純機械改動, 交給 `mech-executor` 去做, 你負責驗收: 改完跑 `python3 -m unittest` 要全綠.
