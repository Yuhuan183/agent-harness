# 標準化指標模型

## Schema v2（`~/.agents/telemetry/experience.jsonl`，每次派工一筆；相容 v1）

| 欄位 | 必填 | 值域 | 說明 |
|---|---|---|---|
| `ts` | ✓ | ISO 8601 UTC | 記帳時間（quality-check 完成時） |
| `role` | ✓ | 七個 leaf role 名 | 派工角色 |
| `provider` | ✓ | `claude` \| `codex` | 實際執行的 provider |
| `outcome` | ✓ | `accepted` \| `corrected` \| `rebriefed` \| `failed` | 主 session 品質判定 |
| `model` / `effort` / `tier` | | | 實際 dispatch 參數（tier: `pinned` \| `follow`） |
| `task_class` | | `recon` \| `plan` \| `impl` \| `verify` \| `security` \| `other` | 任務類型 |
| `task` | | 短中性標籤 | **不含機密與逐字內容** |
| `quality` | | 1–5 | 主觀品質分（可省略） |
| `tokens_in` / `tokens_out` | 自動（可得時） | int | 一般 input/output token |
| `cache_write_tokens` / `cache_read_tokens` | 自動（可得時） | int | cache 建立與讀取 token；四類齊全才計完整 token |
| `secs` | 建議必記 | float | **執行時間代理**：SubagentStart 到 SubagentStop；不含後續主 session 修正與整合 |
| `review_secs` / `rework_secs` | 建議必記 | float | 主 session 品質檢查與修正／整合時間 |
| `api_cost_usd` | 可選 | float | provider 可驗證的本次 API 成本；訂閱方案不填 |
| `note` | | 短句 | 值得記住的意外 |

Outcome 定義：`accepted` 一次過、直接整合；`corrected` 主 session 修過才整合；`rebriefed` 需重派；`failed` 產出棄用或觸發 provider fallback。

## 指標（report 輸出，按 role × provider 分組）

| 指標 | 定義 | 讀法 |
|---|---|---|
| `n` | 樣本數 | n < 5 一律視為證據不足 |
| `AR` | accepted / n | 主指標：一次過率 |
| `CR` / `RB` / `FR` | corrected / rebriefed / failed 佔比 | RB 高 = brief 品質或角色選錯；FR 高 = provider 不適任 |
| `QS` | quality 平均 | 輔助，主觀分 |
| `avg_tokens_out` | 輸出 token 均值 | 算力成本代理；缺 input/cache/單價時不可換算 USD |
| `avg_total_tokens` | 四類 token 合計均值 | 只有四類皆存在的紀錄才納入 |
| `avg_secs` | subagent wall-clock 均值 | **執行時間代理**：同 AR 下越低越好；不含主 session 返工 |
| `avg_total_secs` | subagent＋複核＋返工均值 | 三個時間欄位齊全才納入，更接近 end-to-end |
| `avg_api_cost_usd` | 可驗證 API cost 均值 | 僅比較同計價口徑；不可和訂閱額度互換 |

## 決策規則（provider 選擇的標準化模型）

1. **時間衰減**：每筆紀錄權重 `0.5^(age_days / half_life)`（預設半衰期 45 天，`--half-life 0` 關閉）；AR/CR/RB/FR/QS/均值皆為加權值，舊證據隨 provider 升級自然淡出。
2. 任一 provider 原始樣本 `n < min_samples`（預設 5）→ **explore**：優先派給樣本不足的一方補數據。
3. 兩邊皆足量 → 以衰減後的 accept 計數建 Beta(1+acc, 1+rest) 後驗，算 `P(win)`（固定種子，結果可重現）。`P(win) ≥ prefer_p`（預設 0.85）→ **prefer**；否則 **either**，依序比較 `avg_total_secs`（缺時退回 `avg_secs`）、`avg_api_cost_usd`、`avg_total_tokens`（缺時退回 `avg_tokens_out`）。
4. 規則產出的是 **hint 不是 verdict**——主 session 保留最終判斷，但偏離 hint 時應在 `note` 記下理由，讓偏離本身也成為數據。

## 誠實邊界

- **反事實缺失**：帳本只記「有派工的」，沒有「直接做會如何」的對照組；派工頻率與 nested 違規由既有 `delegation.jsonl`（`delegation-report`）另行覆蓋，兩者互補不重複。
- **品質分主觀**：QS 是主 session 的判定，跨時間可能漂移；AR/RB/FR 以行為定義，較穩。
- **小樣本**：每角色 × provider 到 n≥5 前，一切結論都是探索期雜訊。
- **時間含雜訊**：`secs` 混入排隊、審批等待與人為延遲；跨 provider 比較看均值趨勢，單筆離群不足為據。
- **成本口徑可能不完整**：舊紀錄或 provider 可能缺 input/cache、API cost、人工時間；report 只在欄位齊全時顯示完整代理。訂閱方案、延遲價值與失敗損失仍須另外解讀。
- 帳本是 machine-local 遙測，**永不入庫**；`task` 與 `note` 欄不寫機密。

## 進化節奏

每週（可搭配既有 weekly-integrity 節奏）跑一次 `experience-report --days 30`，對照 `delegation-report`：hint 變動 → 更新 `provider-routing` 的偏好註記；RB 持續偏高的角色 → 回頭修 brief 模板或 cost test 判準。
