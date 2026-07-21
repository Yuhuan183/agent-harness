# Harness Engineering Playbook

> 跨專案方法論（統一維護版；佐證數據見 `harness-engineering-research.md`）。
> Runtime 規則放 `CLAUDE.md`／`AGENTS.md`；角色契約放 `agents/`；按需流程放 `skills/`；
> 本文件只保留可複用的設計與驗證方法。

## 1. 核心立場

Harness engineering 仍然需要，但形態已變：**常駐指令檔縮到只剩模型推不出來的東西**
（目標 40–80 行），其餘走漸進揭露（skills/docs）與確定性機制（hooks/CI）。
肥大指令檔的代價是遵循度，不是錢——每條新規則都稀釋所有其他規則。
判準只有一句：「刪掉這一行會不會犯錯？不會就刪。」

常駐內容只該有四類：① 猜不到的精確指令（命令、環境怪癖）② 非預設慣例
③ 硬性護欄 ④ 外部真值來源與衝突優先序。

## 2. 文件與機制分工

| 位置 | 只放什麼 | 不放什麼 |
|---|---|---|
| `CLAUDE.md` / `AGENTS.md` | 每個 session 都需要的短合約；main-only routing | 長教學、歷史、角色細節、可推斷的結構描述 |
| `agents/*.md` | 單一 leaf role 的自足契約 | main orchestration、要求讀其他合約 |
| `skills/` | 觸發條件明確的按需工作流；深度內容放 `references/` | 每 session 都需要的規則、模型已內建的通用知識 |
| `docs/` | 跨專案指引與 runtime 知識 | 當前任務狀態 |
| `plans/` | 現況、未決項、簡短決策紀錄 | 已落地規則的重複全文 |
| hooks / tests / CI | 確定性 enforcement 與證據 | 需要模型判斷的政策 |

Subagent 可能仍收到全域指令，因此 main-only 段必須短且邊界清楚。
角色檔要自足，不要求 leaf agent 再讀 `CLAUDE.md`、Plan 或 orchestration skill。

## 3. 四個原則

1. **機制勝過提醒**：確定性檢查交給 hook、test、CI；模型負責判斷。
2. **最短驗證迴路優先**：越快得到可觀察證據，模型越能安全自主。
3. **常駐內容都是注意力稅**：規則互相稀釋，只留每 session 必需的。
4. **抓不到蓄意錯誤的機制等於不存在**：hook 要 pipe-test，golden 要 mutation check。

## 4. 指令設計

- 先消除衝突，再新增規則；反應式維護——同一失敗第二次出現才加規則。
- 只寫模型推不出的事；規則說明目的，不重複系統本來就保證的行為。
- Chat Profile 管回答偏好；Cowork 管檔案交付；Claude Code 管改碼與 runtime——不跨平台逐字複製。
- 對話可精簡，產物不可因精簡而不完整。

## 5. 驗證迴路

每個專案都要回答：「改完一行，最快用什麼證明它正確？」

| 專案 | 最短迴路 | 次層 | 最終驗收 |
|---|---|---|---|
| 編譯／演算法 | typecheck + focused test | golden／fixture | 全量 build／實機 |
| Web／UI | typecheck + lint | DOM、computed style 量測 | 多尺寸實機視覺驗收 |
| library／framework | 自身測試 | 消費端 build 與行為 | 下游全量 |
| MCP／工具 | schema／型別 | 合成 request-response contract | 真實 client |
| 資料／數值 | 單元測試 | 確定性 fixture + tolerance | 全量資料 |

秒級檢查前移到 hook；中等成本由 agent 明確執行；慢速或主觀驗收由人執行、agent 供證據。

**Hook 建置**：真實目錄先證明可跑 → 合成 stdin pipe-test（正常/略過/防循環/錯誤）→
`jq -e` 驗設定 → 失敗訊息要回到模型 → 保持秒級 → 新 session 驗載入。

**Golden／snapshot**：確定性合成輸入 → 可比較格式（UI 優先 DOM/computed style）→
record 與 verify 分離 → guard 防靜默 fallback → 三關驗證（連跑穩定、蓄意改動只打中預期、還原全綠）。

## 6. 外部真相與多 repo

對 tracker、設計稿、上游實作記錄四件事：如何讀、何時重抓、衝突時誰優先、完成後如何回寫。
多 repo 另記錄：上下游關係、build 產物傳播、版本釘選與升級 owner；
`dist/` 不進版控就必須明列重建與下游刷新命令。

## 7. Context 與用量

- **靜態負載**：修剪不用的 plugins、MCP、全域 skills、長指令與過長的 skill description。
- **動態流入才是大頭**：大輸出存檔後讀切片；探索交 subagent；main context 收結論不收 dump。
- **長任務**：在收斂點 `/compact`（先落地目標/決策/未決）；複雜工作用
  research → plan → implement 分段新 context；不要把任何固定 context 百分比當成通用失效線。
- **記憶是快照**：引用前重新驗證；行為合約以版控文件為準。
- 用 `scripts/usage-report --days 7` 看診斷訊號，不冒充供應商配額公式。

### 模型與 provider 的成本效益

選擇順序是：任務／harness 相符的成功證據 → 可接受成果率 → wall-clock 與人工返工 →
完整 token 類型與價格。綜合 Intelligence 只作外部先驗；coding 工作看 coding-agent 與 component
評測，不能把基礎模型總分直接當 repository 修改成功率。

比較成本時用「每個可接受成果的預期總成本」，而非輸出單價：API input/output、cache
write/read、重試、人工修正、等待時間與失敗風險都要入帳。訂閱方案與 API pay-per-token 是
不同口徑，不互相代換。外部榜單會更新，日期、模型設定、effort、harness、benchmark 版本與
成本範圍必須一併記錄；本機 `experience-ledger` 的同 role/provider 結果用來覆寫舊先驗。

## 8. Skill 與第三方內容

- 單專案流程放 project skill；跨專案才放全域；模型已內建的通用知識不做 skill。
- Frontmatter description 短而精（1–2 句觸發 + 不適用情境）——它永遠常駐。
- `SKILL.md` 只放路由與主流程；深度資料放 `references/`。
- 重複解釋兩次以上才封裝；不再使用就移除。
- 第三方 skill 安裝前查：外連、shell/eval、寫入面、prompt injection。

## 9. Enforcement 層級與 bootstrap

`Claude hook → pre-commit → CI → monitoring` 攔截點依序變晚；快檢查前移、完整檢查留 CI，
重要規則不能只依賴單機 hook。

新專案 bootstrap：短指令檔（命令/鐵律/陷阱/最短迴路）→ 記錄拓撲與真相源 →
最小 allowlist → 依成本分配 hook/agent/CI/人 → UI 建可量測 preview →
重複工作流才封裝 skill → 每項機制以蓄意錯誤證明有效才算完成。
