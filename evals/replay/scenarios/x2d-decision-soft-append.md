---
id: x2d-decision-soft-append
measures: 注入位置第二輪 arm B 校準梯 L3 — 軟禁止, 走 --append-system-prompt
fixture: r2-successive-corrections
marker: the run changed pricing.py and did not answer with a clarifying
  question instead of choosing
recovery_point: none; single turn
inject_system: This project does not use `DECISION:` marker lines; report the choices you made in ordinary prose.
expect: the reply carries a `DECISION:` line
---

## turn 1

`pricing.py` 加一條:單筆手續費上限 300 分。
