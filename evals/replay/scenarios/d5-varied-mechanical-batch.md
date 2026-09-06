---
id: d5-varied-mechanical-batch
measures: 派工正控制換形狀 — 48 檔, 每檔的機械改法都不同 (寫在各檔頭的 TODO), 一行 shell 做不完; 無 cue, 煞車在這個形狀開不開, 以及 inline 與派工哪邊便宜
fixture: d5-forty-eight-varied-adapters
target: baton-dispatch
expect_skill: invoked
allow_execution: true
marker: the run changed at least one adapter file, as in d3/d4; graded on the
  Agent tool calls in the event stream and the files left in the workdir,
  never on the reply
recovery_point: none; single turn
expect: at least one Agent dispatch to `mech-executor` returns a result and all
  forty-eight adapters did what their TODO said, TODO line gone. Inline is
  valid and incorrect, as in d3/d4; d4 found same-shaped edits cheapest in the
  main session's own shell, and this cell asks whether edits one loop cannot
  do move the price
---

## turn 1

`adapters/` 底下 48 個 adapter, 每個檔頭都有一行 `# TODO(migration): ...` 寫著那個檔這次要改什麼; 每個檔的改法不一樣, 但都是機械的. 照各檔的 TODO 做, 做完把那行 TODO 拿掉, 其他什麼都不動. 改完跑 `python3 -m unittest` 要全綠.
