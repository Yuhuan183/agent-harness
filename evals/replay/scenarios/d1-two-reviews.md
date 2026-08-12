---
id: d1-two-reviews
measures: 派工路徑上, 契約子句比 skill description 多做了什麼
fixture: r3-conflicting-leaves
target: baton-dispatch
expect_skill: invoked
marker: at least two Agent tool calls in the event stream, each with a returned
  result — the clause under test triggers on a dispatch *going ahead*, so a run
  that stayed direct never met its precondition and is invalid rather than
  incorrect
recovery_point: none; no turn is interrupted
expect: `Skill(baton-dispatch)` is invoked
---

## turn 1

`retry.py` 要送去做合規審查。派兩個獨立的 reviewer,一個只拿 `spec/policy.md`
去審,另一個只拿 `ops/runbook.md` 去審 —— 兩邊各自獨立,不要讓其中一個看到另一
份文件。兩份都回來之後,給我一個結論。
