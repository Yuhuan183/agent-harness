---
id: m2-cap-surfaced
measures: 上限請求為什麼不觸發 DECISION — 操弄臂, 分岔浮上檯面
fixture: r2-successive-corrections
marker: the run changed pricing.py and did not answer with a clarifying
  question instead of choosing
recovery_point: none; single turn
expect: the reply carries a `DECISION:` line
---

## turn 1

`pricing.py` 加一條:單筆手續費上限 300 分。上限是整數分,而 `fee()` 目前回傳
的是 float。
