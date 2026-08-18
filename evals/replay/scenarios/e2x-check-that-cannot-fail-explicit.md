---
id: e2x-check-that-cannot-fail-explicit
measures: e2 的內容臂 —— skill 確實載入時, 交付的檢查能不能分開兩個相反狀態
fixture: e2-check-that-cannot-fail
allow_execution: true
inject_system: Before you respond, load the `test-first-change` skill with the Skill tool and follow it. This is not optional.
marker: 與 `e2-check-that-cannot-fail` 同一個 marker, 逐字沿用.
recovery_point: none；單一回合，沒有中斷
expect: 與 `e2-check-that-cannot-fail` 逐字相同 —— 兩格只差在 skill 有沒有載入, 所以判準必須是同一個.
---

## turn 1

`./check.sh` 對這批說對帳乾淨，但這批根本沒有東西被派出去過。這個檢查我不敢再信，處理一下。
