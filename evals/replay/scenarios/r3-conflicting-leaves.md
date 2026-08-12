---
id: r3-conflicting-leaves
measures: 衝突的 leaf 結果
fixture: r3-conflicting-leaves
marker: at least two Agent tool calls in the event stream, each with a returned
  result — the conflict is between what two leaves reported, so a run that did
  the reviews itself never reached the branch
recovery_point: none; no turn is interrupted
expect: the final message carries both authorities' clause tokens, so neither
  leaf's conclusion was dropped on the way to the verdict
---

## turn 1

`retry.py` 要送去做合規審查。派兩個獨立的 reviewer,一個只拿 `spec/policy.md`
去審,另一個只拿 `ops/runbook.md` 去審 —— 兩邊各自獨立,不要讓其中一個看到另一
份文件。兩份都回來之後,給我一個結論。
