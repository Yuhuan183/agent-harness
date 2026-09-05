---
id: d3-stable-mechanical-batch
measures: 派工路徑的 positive control — 該派工時 (12 檔同形機械編輯, 規格完整, 自帶紅測試) 有沒有派給便宜的機械工
fixture: d3-twelve-adapters
target: baton-dispatch
expect_skill: invoked
allow_execution: true
marker: the run changed at least one adapter file. A run that changed nothing
  never reached the point where the brake decides, and is invalid rather than
  incorrect; graded on the Agent tool calls in the event stream and the files
  left in the workdir, never on the reply
recovery_point: none; single turn
expect: at least one Agent dispatch to `mech-executor` returns a result and all
  twelve adapters read `VERSION = 2` afterwards. A run that edits all twelve
  inline is valid and incorrect — every earlier dispatch cell measured the
  brake only from the side where staying direct is right, so this is the first
  reading from the other side, and either result is a finding
---

## turn 1

`adapters/` 底下 12 個 adapter 的 `VERSION` 都要從 1 升到 2, 每個檔的改法完全一樣, 其他什麼都不動. 改完跑 `python3 -m unittest` 要全綠.
