---
name: experience-ledger
description: 派工經驗記帳與分析：QC 後記錄 outcome，累積 role × provider 指標（AR/CR/RB/FR/QS）做數據導向 provider 選擇。觸發：記錄派工結果、依經驗選 provider、看指標。不觸發：派工決策（baton-dispatch）、provider 規則（provider-routing）、token 用量（usage-report）。
---

# Experience Ledger

把「累積經驗決定 Claude or Codex」變成可運作迴路：**派工 → 品質檢查 → 記帳 → 指標 → 下次選擇**。帳本在 `~/.agents/telemetry/experience.jsonl`（machine-local，永不入庫）。

## 記帳（每次派工的 quality-check 之後，一筆）

SubagentStart/Stop hook（`experience-pending.py`）已自動暫存 role、wall-clock 與 session，記帳只需補 outcome：

```bash
~/.agents/skills/experience-ledger/scripts/experience-log \
  --from-pending --outcome accepted --class impl --task "auth refactor" --quality 4
```

- 明確旗標永遠覆蓋 pending 值；重疊完成時 `--from-pending` 會拒絕猜測，須補 hook 產生的 `--dispatch-id`。無 stub 的 native Codex 記錄須補 `--request-source codex`、role、provider 與 route。
- Claude 角色與 Codex bridge 派工**都要記**；outcome 由主 session 的品質判定決定：`accepted`（一次過）/ `corrected`（修過才整合）/ `rebriefed`（重派）/ `failed`（棄用或 fallback）。
- hook 會記錄 `request_source`（`claude-code`／`claude-code-plugin-codex`）、dispatch、rollout、input/output/cache token 與 `secs`（可得時）；native Codex 使用 `codex`。bridge 時窗若碰到多個 rollout，標記 ambiguous 並不寫 token，避免錯帳。品質檢查後補 `--review-secs`、`--rework-secs`；有可靠帳單值才補 `--api-cost-usd`。
- `--task` 用短中性標籤，不寫機密與逐字內容；意外寫進 `--note`。
- 專案定位／盤點用 `--class recon`；具明確攻擊 lens 的對抗式專案審查用 `--class review`，後者預設 full QC。不要因為兩者都由 `Explore` 執行就混在同一 cohort。
- 偏離 report hint 的 provider 選擇，必記 `--note` 說明理由。

## 查詢（provider 選擇不確定時；每週例行一次）

```bash
~/.agents/skills/experience-ledger/scripts/experience-report
```

輸出 role × task class × provider 的 observed/decision n、AR/CR/RB/FR/QS、來源、coverage、成本代理與 hint。只有 schema v3 且來源與 route 完整的 production 紀錄能進決策；舊資料仍顯示但不影響 hint。門檻只由兩側 `model-routing.toml` 的相同 `revision_policy` 驅動；目前為 90 天、45 天半衰期、每格 n≥10、P(win)≥0.90。兩側設定不同或缺欄位時停止。`smoke`／`other` 不產生 hint；成本只比較雙方都有足量的相同口徑。**hint 是方向不是判決**。

Codex 側 token 與額度：`scripts/codex-usage` 讀本機 `~/.codex/sessions/` rollout 的 `token_count` 事件——`--quota` 看帳號窗口用量（重度派工前檢查；短窗口如 5h 優先於週窗口——短窗口耗盡任務直接停擺，接近 90% 就改派 Claude 或等重置），無旗標另附最近 session 的累計與末回合 usage，可作 Codex 派工 `--tokens-out` 的資料源。

Profile 重推：`scripts/experience-revise` 直接讀每側 `revision_policy`，只在目前 deployment profile 的相同 role／task class 比較 route cell，並回報 unsampled／insufficient／keep／consider。工具只建議不改檔；role-wide 調整仍由 main 綜合各 cohort 後決定。

指標定義、schema、誠實邊界與進化節奏見 [references/metrics.md](references/metrics.md)。派工頻率與 nested 違規由既有 `delegation-report` 覆蓋，與本帳本互補。
