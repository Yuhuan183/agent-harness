# QC 白話說明：派工品質怎麼把關

寫給想快速理解「leaf 交回來的東西為什麼可以信」的人。本文只做解釋；有約束力的
規則字面在 [baton-dispatch](../.claude/skills/baton-dispatch/SKILL.md)、
[provider-routing](../.claude/skills/provider-routing/SKILL.md)（Claude 端）與
[leaf-dispatch](../.codex/skills/leaf-dispatch/SKILL.md)（Codex 端），工具是
[qc-gate-lines](../.agents/scripts/qc-gate-lines)。

## 為何需要 QC

coding agent 最有據可查的失敗不是「做不出來」，而是**「宣稱做完了，但沒有」**：
測試被弱化到能過、為了通過檢查捏造 fixture、偷偷改了範圍外的東西，或報告寫得
漂亮但關鍵事實是假的。這不是猜測，是本 repo 自己量出來的：

- s7 假完成 fixture 埋了六種詐欺，說謊報告在無人稽核時可以全身而退；
- s9 取證顯示，opus 檔位的 leaf 約 40% 忘記交代修改依據（INTENT 行整行漏發）、
  10 次有 4 次宣稱「沒有同型 bug」但其實有（TWINS 假陰性）——後者連格式稽核都
  看不出來，因為那行格式完全正確、只是內容是假的。

同時實測也顯示 leaf 的**實質工作幾乎都是對的**（修法正確、不越權、不亂發布）。
所以 QC 的定位不是不信任 leaf 的能力，而是：**報告是一組待證主張，不是證據**。
把「驗證主張」這件事放在便宜的 QC 環節，就能繼續安全地派低檔位、低成本的 leaf。

## 如何運作

每一次派工結束，main session 依序做四件事：

1. **收件與分級。** 取回 leaf 的最終回覆（就是交付物）。機械性工作（規格完整、
   照樣板套用）用 spot 抽查：抽 diff、跑 brief 裡的驗收指令；判斷性或驗證性
   交付一律 full review 逐項對 brief。
2. **機械稽核 owed lines。** 產出實際 diff，餵給 `qc-gate-lines <report>
   --diff <diff>`：工具從 diff 自動判定「改了程式就欠 INTENT 行」（不靠人記得），
   再檢查 TWINS／AUTH 行的在場與格式。漏行或走樣直接是 finding。
3. **抓詐欺清單。** 對照固定清單獵捕：被弱化或繞過的檢查、為過檢查捏造的
   fixture、未申報的範圍外修改、leaf 自建的殘留檔案。特別規則：**TWINS 宣稱
   「found 0/none」一律不憑報告採信**——工具會標 VERIFY，reviewer 必須自己 grep
   修掉的構造掃一遍範圍（這條規則來自 4/10 假陰性的實測）。
4. **裁決與記帳。** 結果四選一：accepted（照收）、corrected（main 修正後收）、
   rebriefed（重派）、failed。絕不默默合併弱交付。裁決連同路由、時間、token 寫入
   experience ledger，累積成 provider 選擇的本機證據；合成的 trap 演練記 `smoke`，
   不污染真實決策數據。

高風險面（安全邊界、金錢、不可逆操作等）另有獨立的 `verifier` 角色做 fresh-context
反證，那是 QC 之上的另一層，每個任務至多一個，觸發條件在 provider-routing。

## 這套設計的取捨

規則放在哪一層是刻意的：leaf 契約只放少量「決策點強制行」（INTENT/TWINS/AUTH，
有 A/B 實驗背書），因為常駐規則會互相稀釋注意力；**謊言與遺漏的攔截責任放在 QC
機制**，因為機制勝過提醒——工具不會忘記設旗標，grep 不會被漂亮的報告說服。
每條 QC 規則都對應一個曾經失敗的 trap 取證（`evals/traps/`），沒有失敗證據的
規則不進清單。

## 規則的證據怎麼來：cross-domain trap

QC 規則不是想出來的，是用行為陷阱量出來的，而且**必須跨領域重測**才算數：

- s7（小數捨入）先量出三種格式失誤並用一句條款修到 3/3——看起來收工了；
- 換到 s9（時區日切）重測，同一批條款當場破功：INTENT 從「格式漂移」變成
  「整行漏發」（~40%），且 s9 內嵌了一個真的同型 bug（`utils.py` 的 twin），
  讓「found 0/none」第一次可以被機械證偽——4/10 的假陰性就是這樣抓到的。
- 教訓：單一 fixture 上的滿分有過擬合成分；條款管得住「怎麼寫」，管不住
  「要不要寫」與「內容真不真」。後兩者交給 QC 機制，正是上面第 2、3 步的由來。

新領域的 trap 都帶 answer sheet 與機械 grader（跑程式、比 diff，從不讀報告下
結論），trap 演練同時也在校準 grader 自己——s9 一輪就修掉了評分器的兩個盲點。

## 總結

- **為何**：假完成是 agent 最常見的失敗；報告是主張、不是證據。
- **如何**：收件分級 → diff 餵機械稽核 → 詐欺清單＋強制 grep → 四級裁決入帳。
- **效果**：盲測中 QC 管線與知道答案的評分器判定 4/4 一致；leaf 失誤變成便宜的
  corrected，而不是缺陷逃逸。
- **代價**：每次派工多一次 diff 稽核與（偶爾的）grep——遠低於一次假完成的返工。
