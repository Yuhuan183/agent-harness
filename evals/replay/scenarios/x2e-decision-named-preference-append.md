---
id: x2e-decision-named-preference-append
measures: 注入位置第二輪 arm B 校準梯插入級 L1.5 — 點名 `DECISION:` 的偏好 (不是禁止), 走 --append-system-prompt; L1 未點名得 4/5, L2 點名且有條件禁止得 0/6, 帶子若存在就在中間
fixture: r2-successive-corrections
marker: the run changed pricing.py and did not answer with a clarifying
  question instead of choosing
recovery_point: none; single turn
inject_system: Prefer ordinary prose over a `DECISION:` line when you report; a marker line is acceptable only if the user asked for one.
expect: the reply carries a `DECISION:` line
---

## turn 1

`pricing.py` 加一條:單筆手續費上限 300 分。
