---
name: experience-ledger
description: 派工經驗記帳與分析：每次子 agent 品質檢查後記錄 outcome，累積 role × provider 的標準化指標（AR/CR/RB/FR/QS），在 Claude 與 Codex 之間做數據導向的 provider 選擇。觸發：記錄派工結果、依經驗選 provider、檢視派工經驗指標。不觸發：派工決策本身（baton-dispatch）、provider 規則（provider-routing）、token 用量分析（usage-report）。
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
- `--tokens-out` 建議必記（可得時）：算力成本是 either hint 的次級 tie-breaker；時間成本（`secs`）由 hook 自動帶入。
- `--task` 用短中性標籤，不寫機密與逐字內容；意外寫進 `--note`。
- 偏離 report hint 的 provider 選擇，必記 `--note` 說明理由。

## 查詢（provider 選擇不確定時；每週例行一次）

```bash
~/.agents/skills/experience-ledger/scripts/experience-report --days 30
```

輸出 role × provider 的 n/AR/CR/RB/FR/QS 與決策 hint（紀錄依 45 天半衰期加權，舊證據自然淡出）。決策規則：樣本 n<5 → explore 補數據；Beta 後驗 P(win)≥0.85 → prefer；否則 either，以成本代理（時間、token）裁量。**hint 是方向不是判決**——主 session 保留最終判斷。

指標定義、schema、誠實邊界與進化節奏見 [references/metrics.md](references/metrics.md)。派工頻率與 nested 違規由既有 `delegation-report` 覆蓋，與本帳本互補。
