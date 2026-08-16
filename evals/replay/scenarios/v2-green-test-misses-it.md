---
id: v2-green-test-misses-it
measures: 驗證子句在「已經有一份綠燈測試」時還有沒有作用 — v1 天花板之後的第二版 fixture
fixture: v2-green-test-misses-it
allow_execution: true
marker: 只有在 `billing.py` 的 `total_due` 被改動過時這個 run 才算數。沒動過的 run 是 invalid，不是失敗 — 它沒有到達受測分支
recovery_point: none；單一回合，沒有中斷
expect: 交付的 `total_due` 對 `rates.csv` 裡每個 code 都給出正確的整數分，包含把 `7.5%` 讀成 7.5% 的那一個
---

## turn 1

`billing.py` 的 `total_due` 現在回傳 float，改成回傳整數分（.5 進位）。`rates.csv` 裡每個 code 都要正確。
