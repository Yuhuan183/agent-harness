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

- 明確旗標永遠覆蓋 pending 值；Codex bridge 派工 stub 無法辨識角色時補 `--role`。無 stub 時退回全手動旗標。
- Claude 角色與 Codex bridge 派工**都要記**；outcome 由主 session 的品質判定決定：`accepted`（一次過）/ `corrected`（修過才整合）/ `rebriefed`（重派）/ `failed`（棄用或 fallback）。
- hook 會帶入 input/output/cache token 與 subagent `secs`（可得時）；品質檢查後補 `--review-secs`、`--rework-secs`，provider 有可靠帳單值時再補 `--api-cost-usd`。缺欄位時 report 會退回較窄的代理，不能冒充完整美元成本。
- `--task` 用短中性標籤，不寫機密與逐字內容；意外寫進 `--note`。
- 偏離 report hint 的 provider 選擇，必記 `--note` 說明理由。

## 查詢（provider 選擇不確定時；每週例行一次）

```bash
~/.agents/skills/experience-ledger/scripts/experience-report --days 30
```

輸出 role × provider 的 n/AR/CR/RB/FR/QS、成本代理與決策 hint（紀錄依 45 天半衰期加權，舊證據自然淡出）。決策規則：樣本 n<5 → explore 補數據；Beta 後驗 P(win)≥0.85 → prefer；否則 either，依「subagent＋複核＋返工時間 → API cost → 完整 token → output token」裁量。**hint 是方向不是判決**——主 session 保留最終判斷。

Codex 側 token 與額度：`scripts/codex-usage` 讀本機 `~/.codex/sessions/` rollout 的 `token_count` 事件——`--quota` 看帳號窗口用量（重度派工前檢查；短窗口如 5h 優先於週窗口——短窗口耗盡任務直接停擺，接近 90% 就改派 Claude 或等重置），無旗標另附最近 session 的累計與末回合 usage，可作 Codex 派工 `--tokens-out` 的資料源。

Profile 重推：`scripts/experience-revise` 讀帳本與兩側 routing 檔（經共用 schema 層），對每個 role 回報 unsampled／insufficient／keep／consider——consider 需該格 n≥5、P(win)≥0.85 且不低於品質底線。工具只建議不改檔；採納後手動改 TOML 並記 decision。

指標定義、schema、誠實邊界與進化節奏見 [references/metrics.md](references/metrics.md)。派工頻率與 nested 違規由既有 `delegation-report` 覆蓋，與本帳本互補。
