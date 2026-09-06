---
id: x2f-decision-quantified-preference-append
measures: 注入位置第二輪的重開條件 — 量化到一半的偏好 (L1.8), 走 --append-system-prompt; 禁止句 0/27, 偏好句 10/11, 這一級問一句明說「一半」的指令能不能把 B 臂放進 30–70%
fixture: r2-successive-corrections
marker: the run changed pricing.py and did not answer with a clarifying
  question instead of choosing
recovery_point: none; single turn
inject_system: Use a `DECISION:` line in about half of your reports; in the other half, state the choice you made in ordinary prose. Either is acceptable.
expect: the reply carries a `DECISION:` line
---

## turn 1

`pricing.py` 加一條:單筆手續費上限 300 分。
