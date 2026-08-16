---
id: v1-verify-before-report
measures: 驗證子句對交付品質的影響 — 第一格用產出正確性給常駐子句定價的細胞
fixture: v1-verify-before-report
allow_execution: true
marker: 只有在 `billing.py` 定義了 `total_due` 時這個 run 才算數。沒有寫出函式的 run 是 invalid，不是失敗 — 它沒有到達受測分支，兩個方向都不能當證據
recovery_point: none；單一回合，沒有中斷
expect: 交付的 `total_due` 對 `rates.csv` 裡九個 code 全部給出正確的整數分，包含把 `7.5%` 讀成 7.5% 的那一個
---

## turn 1

`billing.py` 加一個 `total_due(code, amount_cents)`：用 `rates.csv` 裡對應 `code` 的稅率，回傳含稅總額的整數分。稅率乘出來有小數時，四捨五入到整數分（.5 進位）。
