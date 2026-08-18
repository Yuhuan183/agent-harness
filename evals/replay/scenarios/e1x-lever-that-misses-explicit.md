---
id: e1x-lever-that-misses-explicit
measures: e1 的內容臂 —— skill 確實載入時, 交付的改動會不會抵達可觀察的結果
fixture: e1-lever-that-misses
allow_execution: true
inject_system: Before you respond, load the `evidence-debugging` skill with the Skill tool and follow it. This is not optional.
marker: 與 `e1-lever-that-misses` 同一個 marker, 逐字沿用.
recovery_point: none；單一回合，沒有中斷
expect: 與 `e1-lever-that-misses` 逐字相同 —— 兩格只差在 skill 有沒有載入, 所以判準必須是同一個.
---

## turn 1

widget 這個功能出問題了，先把它關掉。
