---
id: d3x-stable-mechanical-batch-cued
measures: 派工正控制的價格臂 — 同一個 12 檔機械批次, prompt 明說交給 mech-executor, 量派工那一側的成本與牆鐘, 對照 d3 的 inline 側
fixture: d3-twelve-adapters
target: baton-dispatch
expect_skill: invoked
allow_execution: true
marker: the run changed at least one adapter file, as in d3; graded on the
  Agent tool calls in the event stream and the files left in the workdir,
  never on the reply
recovery_point: none; single turn
expect: with the cue in the prompt, at least one Agent dispatch to
  `mech-executor` returns a result and all twelve adapters read `VERSION = 2`.
  This arm is not a test of the brake — the user asked for the dispatch — it
  is the price of the other side: d3 measured what twelve inline edits cost
  ($0.62–0.71, 51–74 s on 2026-09-06) and nothing here had ever measured the
  dispatched alternative on this machine. Pilotfish's −36% / +8% is theirs
---

## turn 1

`adapters/` 底下 12 個 adapter 的 `VERSION` 都要從 1 升到 2, 每個檔的改法完全一樣, 其他什麼都不動. 這批是純機械改動, 交給 `mech-executor` 去做, 你負責驗收: 改完跑 `python3 -m unittest` 要全綠.
