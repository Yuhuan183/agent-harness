---
id: m1-cap-embedded
measures: 上限請求為什麼不觸發 DECISION — 對照臂
fixture: r2-successive-corrections
marker: the run changed pricing.py and did not answer with a clarifying
  question instead of choosing
recovery_point: none; single turn
expect: the reply carries a `DECISION:` line
---

## turn 1

`pricing.py` 加一條:單筆手續費上限 300 分。
