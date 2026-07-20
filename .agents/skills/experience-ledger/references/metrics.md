# 標準化指標模型

## Schema v1（`~/.agents/telemetry/experience.jsonl`，每次派工一筆）

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
| `tokens_out` | | int | 算力成本代理（可得時記） |
| `secs` | 建議必記 | float | **時間成本**：發派到整合完成的 wall-clock（含主 session 修正時間） |
| `note` | | 短句 | 值得記住的意外 |

Outcome 定義：`accepted` 一次過、直接整合；`corrected` 主 session 修過才整合；`rebriefed` 需重派；`failed` 產出棄用或觸發 provider fallback。

## 指標（report 輸出，按 role × provider 分組）

| 指標 | 定義 | 讀法 |
|---|---|---|
| `n` | 樣本數 | n < 5 一律視為證據不足 |
| `AR` | accepted / n | 主指標：一次過率 |
| `CR` / `RB` / `FR` | corrected / rebriefed / failed 佔比 | RB 高 = brief 品質或角色選錯；FR 高 = provider 不適任 |
| `QS` | quality 平均 | 輔助，主觀分 |
| `avg_tokens_out` | 輸出 token 均值 | 算力成本代理 |
| `avg_secs` | wall-clock 均值 | **時間成本代理**：同 AR 下越低越好；corrected/rebriefed 的返工時間已內含 |

## 決策規則（provider 選擇的標準化模型）

1. 任一 provider 樣本 `n < min_samples`（預設 5）→ **explore**：優先派給樣本不足的一方補數據。
2. 兩邊皆足量 → AR 領先 **≥ 10 個百分點**者 **prefer**；差距 <10pt → **either**，以成本代理裁量——**時間（`avg_secs`）優先於 token（`avg_tokens_out`）**，report 會在 either hint 標出較快的一方。
3. 規則產出的是 **hint 不是 verdict**——主 session 保留最終判斷，但偏離 hint 時應在 `note` 記下理由，讓偏離本身也成為數據。

## 誠實邊界

- **反事實缺失**：帳本只記「有派工的」，沒有「直接做會如何」的對照組；派工頻率與 nested 違規由既有 `delegation.jsonl`（`delegation-report`）另行覆蓋，兩者互補不重複。
- **品質分主觀**：QS 是主 session 的判定，跨時間可能漂移；AR/RB/FR 以行為定義，較穩。
- **小樣本**：每角色 × provider 到 n≥5 前，一切結論都是探索期雜訊。
- **時間含雜訊**：`secs` 混入排隊、審批等待與人為延遲；跨 provider 比較看均值趨勢，單筆離群不足為據。
- 帳本是 machine-local 遙測，**永不入庫**；`task` 與 `note` 欄不寫機密。

## 進化節奏

每週（可搭配既有 weekly-integrity 節奏）跑一次 `experience-report --days 30`，對照 `delegation-report`：hint 變動 → 更新 `provider-routing` 的偏好註記；RB 持續偏高的角色 → 回頭修 brief 模板或 cost test 判準。
