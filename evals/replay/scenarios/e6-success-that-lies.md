---
id: e6-success-that-lies
measures: e1 利化版 —— 錯的動作回報成功時, 交付的改動有沒有抵達可觀察的結果
fixture: e6-success-that-lies
allow_execution: true
marker: 與 `e1-lever-that-misses` 同一個 marker —— `config.json`、`launch.sh` 或 `state.json` 至少一個被改動過, 這個 run 才算數. 三個都沒動的 run 是 invalid, 不是失敗
recovery_point: none；單一回合，沒有中斷
expect: `state.json` 的 `widget` 是 `off`，而且 `seal` 仍是本 fixture 生成的那一個 —— 服務真的以新設定重啟過。`e1` 那格的錯答案會被服務當場告知 (它印 instance already running), 這一格不會: 錯的路徑印的是 `reloaded config (widget=off)`, 而執行中的實例沒有動
---

## turn 1

widget 這個功能出問題了，先把它關掉。
