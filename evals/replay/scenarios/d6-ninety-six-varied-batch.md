---
id: d6-ninety-six-varied-batch
measures: 派工形狀的外推檢驗 — d5 的 48 檔各不相同批次放大到 96 檔; d5 讀到 inline 逐檔線性長, 派工幾乎持平, 外推交會在約 90 檔; 無 cue, 煞車在這個大小開不開, 以及哪邊便宜
fixture: d6-ninety-six-varied-adapters
target: baton-dispatch
expect_skill: invoked
allow_execution: true
marker: the run changed at least one adapter file, as in d3/d4/d5; graded on
  the Agent tool calls in the event stream and the files left in the workdir,
  never on the reply
recovery_point: none; single turn
expect: at least one Agent dispatch to `mech-executor` returns a result and all
  ninety-six adapters did what their TODO said, TODO line gone. Inline is valid
  and incorrect, as before; this cell asks whether the crossing d5 extrapolated
  to about ninety files is real
---

## turn 1

`adapters/` 底下 96 個 adapter, 每個檔頭都有一行 `# TODO(migration): ...` 寫著那個檔這次要改什麼; 每個檔的改法不一樣, 但都是機械的. 照各檔的 TODO 做, 做完把那行 TODO 拿掉, 其他什麼都不動. 改完跑 `python3 -m unittest` 要全綠.
