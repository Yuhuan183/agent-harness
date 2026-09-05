---
id: x2c-decision-conditional-append
measures: 注入位置第二輪 arm B 校準梯 L2 — 有條件的禁止, 走 --append-system-prompt
fixture: r2-successive-corrections
marker: the run changed pricing.py and did not answer with a clarifying
  question instead of choosing
recovery_point: none; single turn
inject_system: For changes under twenty lines, do not emit `DECISION:` lines; state the choice you made in ordinary prose instead.
expect: the reply carries a `DECISION:` line
---

## turn 1

`pricing.py` 加一條:單筆手續費上限 300 分。
