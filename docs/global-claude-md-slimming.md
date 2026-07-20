# 全域 CLAUDE.md 瘦身計畫

目標：`~/.claude/CLAUDE.md` 約 2k tokens → 約 600，遵循度優先。
基線快照：本專案 `.claude/CLAUDE.md`（2026-07-20）。

## 逐區塊判定

| 區塊 | 判定 | 處理 |
| --- | --- | --- |
| Working agreement | 保留 | 個人偏好模型推不出，已緊湊 |
| Dispatch 準則 | 精簡 | 留「直接執行是預設 + Workflow 需明確授權」兩條，其餘併入 `baton-dispatch` skill |
| Model & provider routing（H/X、fallback、bridge） | 移出 | 新增 `provider-routing` skill，常駐只留一行觸發描述（IFScale 風險最高區） |
| Role routing 表 | 移出 | 與各 agent frontmatter description 重複；security 例外留一行 |
| Verification routing | 精簡 | 留「高風險面才派 verifier、不疊 gate」，觸發清單移入 skill |
| Markers（DECISION/UNCERTAIN/ERROR） | 視使用率 | 低使用率則刪 |
| headroom 段 | 精簡 | 一行即可 |

## 驗收

挑 3–5 個近期真實任務（含一次跨 provider 交接、一次高風險驗證），
瘦身前後各跑一次，比較：鐵律有無遺漏、routing 是否仍正確觸發、總 token。

## 回寫流程

1. 在本專案 `.claude/CLAUDE.md` 編修並 review diff。
2. 建立 `provider-routing` skill 於 `.claude/skills/`。
3. 兩者一併複製回 `~/.claude/`，跑驗收任務。
