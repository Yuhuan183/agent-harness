# 常駐契約瘦身規範（CLAUDE.md ＋ AGENTS.md）

適用對象：`.claude/CLAUDE.contract.md`（部署為 `~/.claude/CLAUDE.md`）與
`.codex/AGENTS.contract.md`（部署為 `~/.codex/AGENTS.md`）。這是規範而非歷程；
歷次瘦身決策由 Git 與 [orchestration-history.md](../.claude/plans/orchestration-history.md) 保存。

## 原則

1. **常駐只放「每個 session 都需要、且模型推不出」的規則。** 判準是「刪掉會不會讓
   模型犯錯」；會，才留。個人偏好（語言、報告形狀）屬於推不出的一類。
2. **規則競爭注意力。** 常駐檔越長、單條遵循度越低（IFScale／Context Rot 證據見
   [研究摘要](harness-engineering-research.md)）。加一條的成本是其他每一條的稀釋。
3. **分層放置。** 按需流程放 skills（漸進揭露）；可機械判定的紀律交給 hooks 與
   contract tests（機制勝過提醒）；角色專屬規則放各 role 契約，不進主契約。
4. **決策點強制行勝過清單散文。** 弱檔位執行者只遵守決策點上的格式行
   （`INTENT:`／`TWINS:`／`AUTH:`／`LEAF_DISPATCH` 等），不遵守清單中的原則句；
   此類行屬於 role 契約與 QC 檢核，不佔主契約預算（fable-method 蒸餾，取證見
   `evals/traps/`）。
5. **兩契約語意同步、字面各自最短。** Claude 與 Codex 的同一條政策必須語意一致
   （twin-parity 測試鎖定），但照各平台慣用語各自壓縮，不逐字互抄。

## 內容判定表

| 內容類型 | 去向 |
|---|---|
| 語言、報告形狀等個人偏好 | 常駐保留（緊湊、一句一義） |
| 派工剎車與 Workflow 授權底線 | 常駐保留一兩句；細節進 `baton-dispatch` |
| Provider／model routing、fallback、verifier 觸發 | skill（`provider-routing`／`leaf-dispatch`），常駐只留觸發行 |
| Role 能力、工具、停止邊界 | 各 role 契約 frontmatter＋本文；主契約不重複 |
| 可機械檢查的紀律（紅測試不 commit、pin 漂移、owed lines） | hooks／validators／graders，文件只留一行指向 |
| 歷史決策、實驗數據、方法論 | Git、history、docs；永不常駐 |

## 預算與強制

- 預算以 `word_count`（CJK-aware，每個 CJK 字元計一詞）計，行數不可作為預算單位
  （長行可規避）。現行數值的唯一真相源是
  [test_contracts.py](../.claude/tests/test_contracts.py) 的 `DocumentationBudgetTests`；
  本文不複製數字。
- 調高預算需要證據：先嘗試「移出到 skill／hook／role 契約」，只有內容確屬
  「每 session 必要且推不出」時才擴預算，並在 commit message 記明理由。
- 變更預算單位時，必須以新單位重測所有受管檔案後再定數值。

## 驗收

瘦身或增補後：挑 3–5 個近期真實任務（至少含一次跨 provider 交接、一次高風險驗證），
變更前後各跑一次，比較鐵律有無遺漏、routing 是否仍正確觸發、常駐 token 差異。
格式紀律類規則另以 `evals/traps/` 的對應 trap 做 A/B（無失敗 trap 的規則是刪除候選）。

## 回寫流程

1. 在 source checkout 編修（源檔刻意不叫 `CLAUDE.md`／`AGENTS.md`，避免在本 repo 內
   開 session 時與全域版重複載入；sync 時依 manifest 改名部署）。
2. `python3 -m unittest discover -s .claude/tests`（含預算與 twin-parity）全綠。
3. `scripts/sync.sh` dry-run → `--apply` → 開新 session 跑驗收任務。
