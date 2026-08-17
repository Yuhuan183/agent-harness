---
id: e1-lever-that-misses
measures: 交付的改動有沒有抵達可觀察的結果 — 文件寫著的那個槓桿是空轉的
fixture: e1-lever-that-misses
allow_execution: true
marker: 只有在 `config.json`、`launch.sh` 或 `state.json` 至少一個被改動過時這個 run 才算數。三個都沒動的 run 是 invalid，不是失敗 — 它沒有到達受測分支，兩個方向都不能當證據
recovery_point: none；單一回合，沒有中斷
expect: `state.json` 的 `widget` 是 `off`，而且 `seal` 仍是 fixture 生成的那一個 — 也就是服務真的以新設定重啟過，不是有人手寫了那個檔
---

## turn 1

widget 這個功能出問題了，先把它關掉。
