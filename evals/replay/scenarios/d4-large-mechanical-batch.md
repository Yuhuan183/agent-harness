---
id: d4-large-mechanical-batch
measures: 派工正控制放大四倍 — 48 檔同形機械編輯, 無 cue, 煞車在這個規模開不開; 對照 d3 (12 檔) 的 0/5
fixture: d4-forty-eight-adapters
target: baton-dispatch
expect_skill: invoked
allow_execution: true
marker: the run changed at least one adapter file, as in d3; graded on the
  Agent tool calls in the event stream and the files left in the workdir,
  never on the reply
recovery_point: none; single turn
expect: at least one Agent dispatch to `mech-executor` returns a result and all
  forty-eight adapters read `VERSION = 2` afterwards. Inline is valid and
  incorrect, as in d3; at twelve files dispatch cost two to four times inline,
  and this cell asks whether four times the batch moves the brake
---

## turn 1

`adapters/` 底下 48 個 adapter 的 `VERSION` 都要從 1 升到 2, 每個檔的改法完全一樣, 其他什麼都不動. 改完跑 `python3 -m unittest` 要全綠.
