# 常駐契約瘦身規範（CLAUDE.md ＋ AGENTS.md）

適用對象：`main/claude/CLAUDE.contract.md`（部署為 `~/.claude/CLAUDE.md`）與
`main/codex/AGENTS.contract.md`（部署為 `~/.codex/AGENTS.md`）。這是規範而非歷程；
歷次瘦身決策由 Git 與 [orchestration-history.md](../main/claude/plans/orchestration-history.md) 保存。

## 原則

1. **常駐只放「每個 session 都需要、且模型推不出」的規則。** 判準是「刪掉會不會讓
   模型犯錯」；會，才留。個人偏好（語言、報告形狀）屬於推不出的一類。
2. **規則競爭注意力。** 常駐檔越長、單條遵循度越低（IFScale／Context Rot 證據見
   [研究摘要](research/README.md)）。加一條的成本是其他每一條的稀釋。
2b. **矛盾是獨立且更貴的失敗形態。** 稀釋讓規則被忽略；矛盾讓模型花 reasoning 去調和兩條
   互斥指令，更慢、更貴、還常常錯（兩家 2026-07 官方指引同時點名，見
   [供應商官方指引](research/context-and-vendors.md#供應商官方指引2026-07)）。三個推論：
   （a）**契約牴觸供應商 system prompt 時是 bug**，處置是刪契約那一行，不是加字補強；
   （b）重述 system prompt 已保證的行為是純注意力稅，一律刪；
   （c）同一條政策只能有一個真相源，其他位置只放連結。加規則前先找矛盾，不是先找空位。
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
| 跨 session 要記得的個人事實與專案約束 | CLI 自動記憶層；常駐契約不再承擔「怕忘記」 |
| 工具用法與邊界 | 該工具的描述；無法改描述時（本 repo 的 RTK／Headroom）常駐只留一行觸發句 |
| 供應商 system prompt 已保證的行為 | 刪除——重述是稅，牴觸是 bug |
| 歷史決策、實驗數據、方法論 | Git、history、docs；永不常駐 |

## 預算與強制

- 預算以 `word_count`（CJK-aware，每個 CJK 字元計一詞）計，行數不可作為預算單位
  （長行可規避）。現行數值的唯一真相源是
  [test_contracts.py](../main/claude/tests/test_contracts.py) 的 `DocumentationBudgetTests`；
  本文不複製數字。**每一支出貨的 skill 都必須有預算**（新增 skill 未登錄即測試失敗），
  上限取當時實測值加約 2%——它是棘輪，不是研究導出的門檻（研究導不出，見
  [context-and-vendors](research/context-and-vendors.md)）。
- 調高預算需要證據：先嘗試「移出到 skill／hook／role 契約」，只有內容確屬
  「每 session 必要且推不出」時才擴預算，並在 commit message 記明理由。
- 下修預算的證據路徑就是下方〈驗收〉那兩條（真實任務回歸、trap A/B），與上修同源；
  它們未自動化，成本是每次 3–5 個真實任務。**成本高不等於不存在**——不要把「還沒跑」
  說成「沒辦法」。各層餘裕實測與槓桿盤點見
  [resident-context-options.md](research/resident-context-options.md)。
- 變更預算單位時，必須以新單位重測所有受管檔案後再定數值。

## 驗收

瘦身或增補後：挑 3–5 個近期真實任務（至少含一次跨 provider 交接、一次高風險驗證），
變更前後各跑一次，比較鐵律有無遺漏、routing 是否仍正確觸發、常駐 token 差異。
格式紀律類規則另以 `evals/traps/` 的對應 trap 做 A/B（無失敗 trap 的規則是刪除候選）。
**動 skill description 前先跑 [s10-skill-recall](../evals/traps/s10-skill-recall/) 兩臂**：
description 同時是常駐成本與唯一的 routing 面，字數與鑑別度互相拉扯，而鑑別度只有
model-in-the-loop 量得到——測試只能釘住觸發詞在不在，量不出改了措辭之後還分不分得開。
它量的是**鑑別度，不是實際載入行為**（批次分類，非 fresh session 觀測），所以證據不對稱：
**某一臂失敗是強證據**（連這種容易的條件都過不了），**某一臂通過是弱證據**（必要非充分）。
通過不等於可以砍；只有失敗能直接否決一次修剪。

`main/.agents/scripts/python3-run scripts/prompt-surface-census.py --check docs/research/prompt-surface-census.json`
另行鎖定 Claude/Codex 的 resident, dispatch-time skill
與 role body words, UTF-8 bytes, SHA-256. Prompt 變更要刻意刷新 snapshot; census 只證明
surface identity 與大小, 不能取代上述 lifecycle/trap 行為驗收.

矛盾稽核（原則 2b）另外做，因為預算與 trap 都測不到它：對照當期供應商 system prompt
與兩份常駐契約逐條比，找重述與牴觸各一類；`/doctor`（Claude Code）可先跑一次當粗篩，
但它評的是肥瘦不是矛盾，仍需人工對照。CLI 大版本更新後重跑——system prompt 會變，
昨天不重複的句子今天可能重複了。

## 回寫流程

1. 在 source checkout 編修（源檔刻意不叫 `CLAUDE.md`／`AGENTS.md`，避免在本 repo 內
   開 session 時與全域版重複載入；sync 時依 manifest 改名部署）。
2. `main/.agents/scripts/python3-run -m unittest discover -s main/claude/tests`（含預算與 twin-parity）全綠。
3. `scripts/sync.sh` dry-run → `--apply` → 開新 session 跑驗收任務。
