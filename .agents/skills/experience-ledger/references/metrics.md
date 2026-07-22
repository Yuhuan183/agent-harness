# 標準化指標模型

## Schema v3（`~/.agents/telemetry/experience.jsonl`，每次派工一筆；相容 v1/v2）

| 欄位 | 必填 | 值域 | 說明 |
|---|---|---|---|
| `ts` | ✓ | ISO 8601 UTC | 記帳時間（quality-check 完成時） |
| `role` | ✓ | 七個 leaf role 名 | 派工角色 |
| `provider` | ✓ | `claude` \| `codex` | 實際執行的 provider |
| `request_source` | ✓（v3） | `claude-code` \| `codex` \| `claude-code-plugin-codex` | 請求起點與呼叫表面 |
| `dispatch_id` / `rollout_id` | 自動（可得時） | string | 將 outcome、hook 與 provider telemetry 綁到同一次派工 |
| `outcome` | ✓ | `accepted` \| `corrected` \| `rebriefed` \| `failed` | 主 session 品質判定 |
| `profile` / `model` / `effort` | ✓（production decision） | | 實際 route；Claude 由 active deployment preset 補標 |
| `tier` | | `spot` \| `full` | QC 層 |
| `task_class` | ✓ | `recon` \| `plan` \| `impl` \| `verify` \| `security` \| `smoke` \| `other` | 任務類型 |
| `task` | | 短中性標籤 | **不含機密與逐字內容** |
| `quality` | | 1–5 | 主觀品質分（可省略） |
| `tokens_in` / `tokens_out` | 自動（可得時） | int | 一般 input/output token |
| `cache_write_tokens` / `cache_read_tokens` | 自動（可得時） | int | cache 建立與讀取 token；四類齊全才計完整 token |
| `token_scope` | 自動 | `full` \| `output_only` \| `partial` | 明示成本代理口徑，禁止跨口徑比較 |
| `telemetry_warning` | 自動（異常時） | string | 例如多個 Codex rollout 同時落入時窗 |
| `secs` | 建議必記 | float | **執行時間代理**：SubagentStart 到 SubagentStop；不含後續主 session 修正與整合 |
| `review_secs` / `rework_secs` | 建議必記 | float | 主 session 品質檢查與修正／整合時間 |
| `api_cost_usd` | 可選 | float | provider 可驗證的本次 API 成本；訂閱方案不填 |
| `note` | | 短句 | 值得記住的意外 |

Outcome 定義：`accepted` 一次過、直接整合；`corrected` 主 session 修過才整合；`rebriefed` 需重派；`failed` 產出棄用或觸發 provider fallback。

## 指標（report 輸出，按 role × task class × provider 分組）

| 指標 | 定義 | 讀法 |
|---|---|---|
| `n` | 可比較樣本數 | 目前 n < 10 一律視為證據不足 |
| `AR` | accepted / n | 主指標：一次過率 |
| `CR` / `RB` / `FR` | corrected / rebriefed / failed 佔比 | RB 高 = brief 品質或角色選錯；FR 高 = provider 不適任 |
| `QS` | quality 平均 | 輔助，主觀分 |
| `avg_tokens_out` | 輸出 token 均值 | 算力成本代理；缺 input/cache/單價時不可換算 USD |
| `avg_total_tokens` | 四類 token 合計均值 | 只有四類皆存在的紀錄才納入 |
| `avg_secs` | subagent wall-clock 均值 | **執行時間代理**：同 AR 下越低越好；不含主 session 返工 |
| `avg_total_secs` | subagent＋複核＋返工均值 | 三個時間欄位齊全才納入，更接近 end-to-end |
| `avg_api_cost_usd` | 可驗證 API cost 均值 | 僅比較同計價口徑；不可和訂閱額度互換 |

## 決策規則（provider 選擇的標準化模型）

1. **時間衰減**：每筆紀錄權重 `0.5^(age_days / half_life)`（目前半衰期 45 天）；AR/CR/RB/FR/QS/均值皆為加權值，舊證據隨 provider 升級自然淡出。視窗、樣本數、半衰期與偏好機率只讀兩側相同的 `revision_policy`；缺欄位或值不同即停止。
2. 只有 schema v3 且具有效 `request_source`、`profile`、`model`、`effort` 的 production 紀錄可進決策；舊版／不完整紀錄保留在 `observed_n` 與來源 coverage 供診斷。`smoke`／`other` 不得產生 provider 或 route hint。
3. provider hint 只比較兩側 `selection.default` 的目前 route cell；同一 role／task class 任一 provider 的該 cell 原始樣本 `n < min_samples`（設定目前為 10）→ **explore**，不得把其他 profile／model／effort 的樣本湊足門檻。
4. 兩邊皆足量 → Beta 後驗 `P(win)` 達設定門檻（目前 0.90）才 **prefer**；否則 **either**。成本 tie-break 只在雙方同一欄位都達樣本門檻時比較，絕不混用 total/output token。
5. 規則產出的是 **hint 不是 verdict**；偏離 hint 時在 `note` 記理由。

## 誠實邊界

- **反事實缺失**：帳本只記「有派工的」，沒有「直接做會如何」的對照組；派工頻率與 nested 違規由既有 `delegation.jsonl`（`delegation-report`）另行覆蓋，兩者互補不重複。
- **品質分主觀**：QS 是主 session 的判定，跨時間可能漂移；AR/RB/FR 以行為定義，較穩。
- **小樣本與任務混淆**：每 role × task class × provider 到 policy 門檻前都是探索期；即使達標，未配對任務仍須 main 判斷難度差異。
- **來源不是可交換樣本**：report 會顯示 `request_sources` 分布；native Codex 與 Claude plugin bridge 即使使用同一 route，也可能有不同 context、排隊與主 session 複核條件。來源組成差異明顯時，不把聚合成本當成乾淨對照，應另外抽同 brief 樣本。
- **時間含雜訊**：`secs` 混入排隊、審批等待與人為延遲；跨 provider 比較看均值趨勢，單筆離群不足為據。
- **成本口徑可能不完整**：舊紀錄或 provider 可能缺 input/cache、API cost、人工時間；report 只在欄位齊全時顯示完整代理。訂閱方案、延遲價值與失敗損失仍須另外解讀。
- 帳本是 machine-local 遙測，**永不入庫**；`task` 與 `note` 欄不寫機密。
- pending hook 與 outcome logger 以同一個 lock 序列化 append／consume；重疊完成仍須用 `dispatch_id` 精確配對。logger 驗證後會以首次讀到的完整 stop stub 清理，因此中途新增 completion 不會改變目標；但 ledger append 與 pending rewrite 是兩個檔案，程序在兩者之間崩潰時仍可能留下已記帳 stub，需依 `dispatch_id` 人工去重。

## 進化節奏

每週（可搭配既有 weekly-integrity 節奏）跑一次 `experience-report`，對照 `delegation-report`：hint 變動 → 更新 `provider-routing` 的偏好註記；RB 持續偏高的角色 → 回頭修 brief 模板或 cost test 判準。`experience-revise` 也只使用目前 deployment profile 內的 route cells，避免把 fast 與 quality-guarded 的不同風險分布混在一起。政策調整只改兩側相同的 `revision_policy`，不從 CLI 臨時覆寫。
