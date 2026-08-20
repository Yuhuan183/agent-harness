# Orchestration current state

> Current as of 2026-08-20. 決策歷程在 [orchestration-history.md](orchestration-history.md);
> 完整差異由 Git 保存.

這份文件只做一件事: **把必須成立的不變量收成一張可以逐條檢查的表**. 每一條的論證, 實作與
量測都不在這裡, 在右欄那份文件裡 —— 這是清單, 不是說明.

它和[分層剖析](../architecture/architecture.md)的分工是刻意的: 分層剖析按**讀者想理解
什麼**組織, 這張表按**改動前後要檢查什麼**組織. 同一批性質, 兩種用途.

## Active invariants

| # | 必須成立的 | 擁有者 |
|---|---|---|
| 1 | 一個可寫 artifact 一個 owner; 單一未知 bug 的診斷, 首次修復與現場驗證留在同一條推理鏈 | [graph](../architecture/graph-engineering.md) |
| 2 | Leaf agent 從不再派工. Claude 側由 `leaf-redispatch` 擋, Codex 側是 `agents.max_depth = 1` | [harness](../architecture/harness-engineering.md) |
| 3 | 每個 top-level task 至多一個 outcome verifier, 放在最小完整驗收邊界 | [loop](../architecture/loop-engineering.md) |
| 4 | Claude 的 no-write 角色沒有 Bash; 需要跑命令的獨立驗證改派 Codex read-only sandbox | [harness](../architecture/harness-engineering.md) |
| 5 | 安全分析在核准契約存在之前一律唯讀; 之後由單一 security executor 實作 | [harness](../architecture/harness-engineering.md) |
| 6 | 同一個 readiness-unit 至多兩次自動實質修訂, 之後把選項交還使用者 | [loop](../architecture/loop-engineering.md) |
| 7 | 固定 `[LEAF_DISPATCH]` / `[LEAF_RESULT]` 紀錄帶 task identity, 完整 route, `request_source`, QC 結果與對應的 ledger identity | [graph](../architecture/graph-engineering.md) |
| 8 | Provider/model 效率決策在 same-role, same-task-class 的 route cell 達到樣本門檻前保持探索 | [證據](../architecture/architecture.md#證據-憑什麼算數) |

八條的共同點是**違反時不會自己冒出來**: 少一個 owner 不會報錯, 多一個 verifier 不會變慢到
被發現, 少一行紀錄要等到對帳才看得見. 需要機制或紀律才成立的性質, 才進這張表.
