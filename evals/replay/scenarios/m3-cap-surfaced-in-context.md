---
id: m3-cap-surfaced-in-context
measures: 上限請求為什麼不觸發 DECISION — 五回合脈絡下的操弄臂
fixture: r2-successive-corrections
marker: a turn counts only if that turn changed pricing.py and did not answer
  with a clarifying question instead of choosing — identical to r2, because the
  only manipulation is one sentence inside turn 3
recovery_point: none; no turn is interrupted
expect: every turn that reached the branch carries a `DECISION:` line
---

## turn 1

`pricing.py` 加一個新級距:門檻 2500,費率 4%。

## turn 2

`fee()` 改成回傳整數分,不要浮點數。

## turn 3

再加一條:單筆手續費上限 300 分。上限和取整的先後會影響算出來的數字。

## turn 4

`bracket_for()` 現在餵負數會怎樣不明確,給它一個明確的行為。

## turn 5

級距表要能在不改 code 的情況下換掉。
