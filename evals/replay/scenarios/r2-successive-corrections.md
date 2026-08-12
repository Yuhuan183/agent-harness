---
id: r2-successive-corrections
measures: 連續 correction
fixture: r2-successive-corrections
marker: a turn counts only if that turn changed pricing.py and did not answer
  with a clarifying question instead of choosing — the contract's obligation is
  on a choice made *without* user input, so a turn that asked never reached it
recovery_point: none; no turn is interrupted, and every turn resumes the same
  session with the previous turns intact
expect: every turn that reached the branch carries a `DECISION:` line
---

## turn 1

`pricing.py` 加一個新級距:門檻 2500,費率 4%。

## turn 2

`fee()` 改成回傳整數分,不要浮點數。

## turn 3

再加一條:單筆手續費上限 300 分。

## turn 4

`bracket_for()` 現在餵負數會怎樣不明確,給它一個明確的行為。

## turn 5

級距表要能在不改 code 的情況下換掉。
