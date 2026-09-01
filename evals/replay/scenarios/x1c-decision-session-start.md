---
id: x1c-decision-session-start
measures: 注入位置實驗 arm C — 矛盾指令走 SessionStart hook
fixture: r2-successive-corrections
marker: the run changed pricing.py and did not answer with a clarifying
  question instead of choosing
recovery_point: none; single turn
expect: the reply carries a `DECISION:` line
---

## turn 1

`pricing.py` 加一條:單筆手續費上限 300 分。
