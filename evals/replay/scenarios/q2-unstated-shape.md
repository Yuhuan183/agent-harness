---
id: q2-unstated-shape
measures: 請求不講形狀時, 派工的形狀與結論品質
fixture: q2-unstated-shape
marker: turn 2 produced a parseable answer. Nothing about dispatching is a
  marker here — whether the session split the work, and whether it kept the
  halves apart, is the observation, so requiring it would delete the comparison
  group this scenario exists to have
recovery_point: none; no turn is interrupted
expect: all five planted contradictions named as clause pairs, none of the three
  near misses claimed, and no pair invented
---

## turn 1

`payments/deliver.py` 下週要過稽核。`spec/policy.md` 和 `ops/runbook.md` 兩份
都管得到它。

我要知道的是:這兩份文件有沒有哪些地方是**同時滿足不了**的 —— 有的話,是哪幾條
對上哪幾條。

## turn 2

把結論收成固定格式,一行一組,只列真的互斥的那些:

    <clause-id> x <clause-id>

說明寫在那些行以外,不要寫進行內。
