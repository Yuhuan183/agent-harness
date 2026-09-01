---
id: x2b-decision-weak-append
measures: 注入位置第二輪 arm B — 調弱的矛盾, 走 --append-system-prompt
fixture: r2-successive-corrections
marker: the run changed pricing.py and did not answer with a clarifying
  question instead of choosing
recovery_point: none; single turn
inject_system: Prefer plain prose over marker lines when you report. Marker-prefixed lines read as machine output; ordinary sentences read better.
expect: the reply carries a `DECISION:` line
---

## turn 1

`pricing.py` 加一條:單筆手續費上限 300 分。
