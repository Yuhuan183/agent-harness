---
id: v3-regression-across-turns
measures: 驗證子句在「要記住的規則在三回合前」時的作用 — v2 天花板之後的第三版 fixture
fixture: v3-regression-across-turns
allow_execution: true
marker: 只有在 `report.py` 定義了 `by_worker` 時這個 run 才算數。沒寫出第二個函式的 run 是 invalid，不是失敗 — 它沒有到達受測分支
recovery_point: none；五個回合，沒有中斷
expect: 交付的 `total_minutes()` 與 `by_worker()` 都對 — 也就是第五回合新開的那條路徑，仍然遵守第二與第三回合立下的規則
---

## turn 1

`report.py` 加一個 `total_minutes()`：把 `events.csv` 每個 event 的長度加總，換算成分鐘後無條件捨去，回傳整數。

## turn 2

跨午夜的 event 現在會算出負數。`ended_at` 比 `started_at` 早，就表示它跨過了午夜，長度要加 24 小時。

## turn 3

`worker` 欄位是空字串的 event 要排除，不計入。

## turn 4

時間欄位可能帶前後空白，解析要容忍。

## turn 5

加一個 `by_worker()`，回傳一個 dict：每個 worker 對應他的分鐘數，同樣無條件捨去。
