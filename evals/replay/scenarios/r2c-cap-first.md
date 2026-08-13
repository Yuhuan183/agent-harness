---
id: r2c-cap-first
measures: 連續 correction — 位置與內容的解耦
fixture: r2-successive-corrections
marker: a turn counts only if that turn changed pricing.py and did not answer
  with a clarifying question instead of choosing — identical to r2 and r2b,
  because the only manipulation is the order of the five requests
recovery_point: none; no turn is interrupted
expect: every turn that reached the branch carries a `DECISION:` line
---

## turn 1

`pricing.py` 加一條:單筆手續費上限 300 分。

## turn 2

再加一個新級距:門檻 2500,費率 4%。

## turn 3

`fee()` 改成回傳整數分,不要浮點數。

## turn 4

`bracket_for()` 現在餵負數會怎樣不明確,給它一個明確的行為。

## turn 5

級距表要能在不改 code 的情況下換掉。
