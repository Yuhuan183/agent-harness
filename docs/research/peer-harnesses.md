# 同業 agent harness 拆解

> 對齊日期: Pilotfish 段 2026-08-08 (v1.3.10); Deep Agents 段 2026-08-08 (0.7.5). 只保留會影響本專案設計的存續結論.

## 這份文件回答什麼

看兩個同類專案, 各自解決什麼問題, 本專案抄了什麼, 為什麼有些不抄.

| 專案 | 它是什麼 | 本專案主要拿走什麼 |
|---|---|---|
| LangChain Deep Agents | 一組可組合的 middleware 與 state boundary, 不是固定流程 | allowlist 優於 denylist; report 與 tool output 視為 untrusted observation |
| Pilotfish | 一套完整的 agent 派工契約, 版本迭代快 | 派工形狀, Plan anti-churn, verdict 三分, prompt 尺寸當常設預算 |

貫穿全文的一條限制: **方法可借, 數字不可借.** 上游的 Gate 數字是它的契約在它的 client 版本上的觀察, 引用時必須連同它自己標的限定一起引.

## LangChain Deep Agents

查核版本: PyPI stable `0.7.5` (2026-08-06). 0.7.x 全是修補與小功能, 沒有新的 middleware. 值得記的變動在同源 CLI `deepagents-code` 0.1.52: Hooks v2 轉正式並支援 plugin 安裝的 hook, 且 HITL 的拒絕理由改寫成給模型看的形式 - 最後這項與 Anthropic auto mode 的 deny-and-continue 是同一件事, 兩個獨立實作收斂 (見 [研究摘要方向 5](README.md#待辦方向)).

Deep Agents 的價值不在提供另一套固定流程, 而在把幾個可組合能力做成 middleware 與 state boundary:

- tool/subagent allowlist 比 denylist 更可證明;
- filesystem, state, memory, human-in-the-loop 各自有清楚生命週期;
- context 壓縮與摘要是執行期能力, 不等於可任意改寫 provider 的 compact payload;
- rubric/grader 的輸入是待驗證 observation, 不是可信 instruction;
- persistence 與 hosted product 的能力, 區域與 beta 狀態需分開陳述.

### 專案採用

- no-write role 使用工具 allowlist.
- report 與引用的 tool output 都視為 untrusted observation.
- compact 後以 `SessionStart[source=compact]` 補最低限度 reseed; 不宣稱能控制 PreCompact 摘要內容.
- memory, ledger 與 Git ownership 分層: Git 保存可攜契約, ledger 保存 machine-local outcome evidence.

### 不採用

- 不導入完整 Deep Agents runtime; 目前 Claude/Codex 原生 agent surface 已足以承載角色契約.
- 不把 hosted/beta 能力寫成穩定, 自架或跨區皆可用.
- 不把一般 middleware pattern 複製成 resident prompt; 只有能改善本專案失敗形態者才落地.

## Pilotfish v1.3.0-v1.3.10

研究基準為 [Pilotfish v1.3.10](https://github.com/Nanako0129/pilotfish/releases/tag/v1.3.10), tag commit `7a7f71b327f079fecbf29fa91e444b9a6180c31c` (2026-08-08). 前一次對齊為 v1.3.8 (`ad9600c...`, 2026-08-04). v1.3.0 到 v1.3.4 的逐版變動已收斂成以下仍存續的原則:

1. **工作形狀決定派工**: 同型, 互相獨立, 能由一份 stable one-shot brief 完整描述, 才適合合批.
2. **未知 bug 不切斷推理鏈**: root cause, 第一個 minimal fix, live verification 留在同一 owner.
3. **mechanical default 可被反駁**: 已知修法的大量機械工作可交給 `mech-executor`; 若 context 重建或整合成本較高, main 直接做.
4. **Plan envelope 與 slice 分離**: 共享 constraints 固定, 下一個可執行 slice 有 stable ID, owner, prerequisites, acceptance, rollback.
5. **readiness 與 outcome 分工**: `plan-verifier` 只判 Plan; `verifier` 只判完成 claim.
6. **anti-churn**: 同 readiness unit 最多兩次自動實質修訂, 之後呈現選項.
7. **安全分權**: read-only security review 先進 Plan, 批准後只有一個 writer.
8. **prompt surface 分層**: resident contract, on-demand skill, leaf role 分開計量與去重.

### v1.3.5-v1.3.8 增量

9. **verdict 三分與嚴重度閘** (v1.3.5): outcome verifier 回 `CONFIRMED`/`REFUTED`/`INCONCLUSIVE`; 只有可重現的 P0-P2 blocker 能推翻 claim, P3/P4 只作建議, 最終處置權留在 main. 長自主執行宣告 `AUTO` 或 `ASK`, 但不因此取得額外權限. 阻斷性 P1/P2 的修復共用五次 pass 預算, 且重驗前必須有變動過的 candidate-state fingerprint - 未改動就重試不算一次機會.
10. **readiness epoch** (v1.3.6): 兩次自動 `REVISE` 後不是硬停. 有實質修正, 收窄, 拆分或新證據時記一個新的 readiness epoch, 並可再要求「剛好一次」全新 readiness check. 再次 `REVISE` 就暫停或升級, 不重開自動迴圈.
11. **prompt 尺寸是常設預算, 不是一次性壓縮** (v1.3.7): #27 在 v1.3.4 砍掉 24.653% 常駐 policy, 但樹裡沒有任何東西能因為尺寸而擋下 release, 到 v1.3.6 policy 已長回壓縮前之上 (bytes/rule: v1.3.3 649.0 -> v1.3.4 489.0 -> v1.3.5 474.3 -> v1.3.6 544.2). 修法是把兩個**正規化**指標寫進測試: 每條規則 UTF-8 bytes <= 500 且規則數釘在 36, contraction 正規化後的贅詞比例 policy <= 10.5%/八個 role 檔 <= 12.0%. 用兩個指標是因為各自堵住對方的作弊路徑 - 只刪虛詞能大幅改善贅詞比例卻幾乎不減 bytes, 把一條規則拆成多個 bullet 則能壓低 bytes/rule 而不動贅詞比例.
12. **dispatch brake 優先於 explicit opt-in** (v1.3.8): 建議的顯式 opt-in 改成要求模型遵守 dispatch brake, 而不是把每個「可派」的任務都派出去. 四條隨之而來:
    - 風險觸發條件在「小工作走捷徑」之前先判.
    - 穩定的機械性重複交給**一個**且必須回收的 `mech-executor`.
    - 例行文件與單一未知 bug 留在 main.
    - schema 類工作的強制 Plan/outcome review 與「誰來實作」的 brake 決策分開處理.

### v1.3.9-v1.3.10 增量

13. **互動模式先於工作者選擇** (v1.3.9): 在 Baton, 生命週期與工作者之前先選互動形狀, 取第一個吻合的 - 結果不明走 `co_discover`, 方向廣或影響大走 `explore_then_plan` (第一回合維持唯讀, 只回一個可逆切片), 結果有界才走 `execute`. 執行只在對應的 readiness Gate 為 `READY` 時才走到 `user_approval`, 否則回報實際卡住或暫停在哪個 Gate. 設計來自 pilotfish-codex PR #14.
14. **cue-free 限制被寫進文件** (v1.3.9): 更高優先級的 client 指令能壓過 Agent 派工, 而 user 層 `CLAUDE.md` 蓋不過它. 上游因此撤下「自動派工」的宣稱, 改成提供顯式的 `/pilotfish` 與 CLI wrapper 兩條啟用路徑. 同一版把 v1.3.8 之後加的 dispatch-rate harness 整個 revert.
15. **壓縮過的政策要重新做行為認證, 候選要綁回被測位元組** (v1.3.9 -> v1.3.10): v1.3.9 把主政策從 18,477 砍到 15,841 bytes (-14.3%), 37 個語意規則單位一個沒少, 但**出貨的那份只有靜態覆蓋** - 行為矩陣跑的是舊的 18,477 快照. 上游自己在 release 裡標明這件事, 沒有把行為結果掛到新位元組上. v1.3.10 才對 15,841 的那份重跑完整 explicit-opt-in 矩陣, 並把候選以「只差版本標記」的正規化綁回被測快照, 兩種形式都納入測試.

### 上游 runtime 證據的新進展

v1.3.4 已有 Gate, v1.3.6 之後改成對整條生命週期實跑並公開逐次嘗試. 可引用的觀察:

| 版本 | 跑了什麼 | 觀察到的結果 | 回報成本 |
|---|---|---|---|
| v1.3.6 | schema migration 走完 `plan-verifier` -> 批准 -> `executor` -> `verifier`, 例行文件維持 direct | 實際跑出 `REVISE` -> `REVISE` -> 新 readiness epoch -> 收尾 `READY` | 現行控制 $2.82515035; 含失敗與被取代的整輪 campaign 為 $5.16072710 |
| v1.3.7 | `verifier-boundary` Gate 對「實際出貨的 bytes」重跑 (不是刷新雜湊) | 三個 cell 都重現; schema cell 2/2 停在批准閘, 批准前無寫入; 再前景派一個 `mech-executor` 與一個 `verifier` 並回收 `CONFIRMED` | - |
| v1.3.8 | policy replay | 例行文件與單一 bug 對照組 2/2 維持 direct, 機械性重複 2/2 派工, schema 2/2 保住 Plan review/批准/主要測試/outcome review | 十次完成的 invocation $3.89565485, 硬上限 $8 |
| v1.3.9 | 對 18,477-byte adaptive-routing 快照跑同一矩陣 | 三格各 2/2; 但**出貨的 15,841 沒跑**, 只有 39/39 靜態測試 | 十次 invocation $4.23888905; 另三次針對修復候選的 TUI 檢查 $1.68 |
| v1.3.10 | 對 15,841-byte 出貨快照重跑完整矩陣 | 三格各 2/2; schema 兩輪都走完 `plan-verifier READY` -> 批准停點 -> 主要測試 4/4 -> `verifier CONFIRMED`; 候選 41/41 靜態測試且標記正規化後位元組相符 | 十次 invocation $3.79160515, 硬上限 $8 |

v1.3.8 那輪期間 Claude Code 自 2.1.220 更新到 2.1.221; v1.3.9 與 v1.3.10 兩輪都在 2.1.224, Opus 5, high effort.

上游自己標註這些是**有界的 reachability 觀察, 不是確定性行為, 不是派工率**, 也不是因果性的檔案所有權歸屬. 這個限定要一起引用, 否則就變成我們替它誇大.

同樣值得記的是它公開的兩個失敗形態:

- 語意缺陷還在時, 批准閘曾在 4 次中被跳過 2 次.
- 某個修訂版本上有一次把驗證派到背景後從未回收 (該版完整驗收 1/2).

另外 v1.3.8 修正了自己的回溯分類器, 把 child-agent 工具與 main session 分開, 並比對已完成的 Agent 結果. 歷史結果由 0/20 更正為 7/20 通過 dispatch-reachability. 但二十次嘗試最終都落在同樣的十二個修改路徑與 12/12 fixture 測試.

### 與本專案的比較

| Pilotfish 存續設計 | 本專案現況 | 裁決 |
|---|---|---|
| shape-based batching | `baton-dispatch` 已採 shared context/artifact/dependency/verification surface | 已落地 |
| direct-execution brake | resident contract 已以淨收益判斷派工 | 已落地 |
| envelope + executable slice | Plan contract 已要求 stable boundary; rollback 由實際 release strategy 決定 | 已落地 |
| Plan anti-churn | 兩次 automatic revision 上限 | 已落地 |
| readiness/outcome 分工 | Claude/Codex twin roles 與 vocabulary tests | 已落地 |
| security sequencing | reviewer → approved contract → single executor | 已落地 |
| fixed dispatch/result records | 兩側 dispatch skill 與 experience ledger | 已落地 |
| exact prompt compression evidence | words/bytes/hash census | 已落地 (靜態) |
| lifecycle behavior proof | interruption, repeat correction, conflicting results replay | 尚缺實證; 開跑前的存活判準見 [lifecycle-replay.md](lifecycle-replay.md) |
| verdict 三分 (v1.3.5) | `verifier` 契約已回 CONFIRMED/REFUTED/INCONCLUSIVE, Claude 與 Codex 雙側一致 | 已落地 |
| 嚴重度閘: 只有 P0-P2 能 refute (v1.3.5) | `verifier` 兩端都要求反例「可重現**且會改變驗收結論**」, 其餘可重現缺陷列 `Advisory:` 照報但不動 verdict; 不引進嚴重度分級 | 已落地, 收斂成一條判準 |
| 五次 pass 預算 + candidate-state fingerprint (v1.3.5) | `baton-dispatch`/`leaf-dispatch` 已寫入五次上限, 且每一 pass 要先講出上一次之後改了什麼, 沒改的候選不重驗 | 已落地, 指紋改用自述 |
| readiness epoch + 一次最終 fresh check (v1.3.6) | `baton-dispatch` 為同 readiness-unit ID 兩次自動修訂後停下呈現選項 | 維持現況 (更嚴格, 不放寬) |
| 常設 prompt 尺寸預算 (v1.3.7) | per-document 字數上限 (claude 520/codex 550), resident-layer 總量, `ROLE_BODY_BUDGET`, 另加規則條數/每條位元組/虛詞比例三項密度指標 | 已落地, 口徑不同 |
| foreground 回收 (v1.3.7 失敗形態) | resident contract 要求 leaf 只跑有界前景命令, role body 另有 10 分鐘上限 | 已落地 |
| brake 壓過 explicit opt-in (v1.3.8) | resident contract 以淨收益判斷派工, `Workflow` 需使用者明示 opt-in | 已落地 |
| 互動模式先於工作者 (v1.3.9) | 無等價; client 自身的 plan mode 已承擔「廣泛請求先唯讀」 | 不採用 (理由見[研究摘要](README.md#明確不做的事)) |
| cue-free 限制 (v1.3.9) | 尚未寫下; 本專案同樣部署 user 層契約 | **採用**, 本機另有當下可觀察的實例 |
| 出貨位元組的行為認證與候選綁定 (v1.3.9 -> v1.3.10) | census 已算 per-file `sha256` 與 `payload_sha256`; trap 結果表沒有指紋欄 | **改造後採用**, 接線既有指紋而非新建 |

### 關鍵修正

早期本專案為了讓 Claude verifier 執行重現, 設計 `readonly-bash` shell parser. 2026-07-28 security review 證明它可被 Git callbacks, environment indirection, parameter expansion, executable resolution 與非 Git 工具副作用繞過. 最終裁決不是繼續擴大 denylist, 而是移除 Claude no-write roles 的 Bash; 需要命令的獨立 verdict 轉給 Codex `sandbox_mode = "read-only"`.

這個結果也修正了對「allowlist」的理解: tool-level allowlist 有有限且可列舉的能力面; shell command parser 面對的是可組合語言與外部程式, 不能提供同等保證.

第二個修正來自上游 v1.3.7, 直接打到本專案的假設: **短語斷言擋不住語意反轉**.

上游那輪壓縮通過了全部 255 條契約測試斷言的短語, 逐字保留, 卻仍帶進十二個語意缺陷:

| 缺陷 | 做了什麼 | 後果 |
|---|---|---|
| 1 處 | 把選言改成連言 | `REJECT` 這個處置變成不可達 |
| 2 處 | 把獨立審查的觸發條件與「使用者親自要求判斷」擴大 | 變成任何使用者請求與泛稱的「user-requested judgment」, 等於把一般可派工作也吃進來 |
| 13 處 | 刪掉範圍限定詞 (`only`, `after`, `each time` 之類) | 後續掃過全部 36 條規則才找到 |

**這些全部是人工逐句對照與外部審查抓到的, 不是測試抓到的.**

本專案的 `test_contracts.py` 同樣以「短語存在」為主要保護. 所以壓縮常駐契約時不能只跑測試: 必須對壓縮前後做逐句對照, 特別檢查連接詞, 範圍限定詞與否定詞 - 這三類的改動不會動到任何被斷言的短語.

第三個修正來自 v1.3.9 與 v1.3.10 的落差, 是上面那一條的時間軸版本: **靜態測試綠燈不等於出貨的那份位元組被行為認證過**. v1.3.9 的 39/39 靜態測試跑的是新政策, 而 6/6 的行為結果跑的是舊快照; 兩個數字擺在同一篇 release note 裡, 讀起來像同一份東西通過了兩種檢查. 上游自己標了限定並在下一版補跑, 但沒有標的話, 這種組合無法從外部分辨. 本專案的形狀完全相同: 275 條靜態斷言隨改隨跑, s7 的行為結果只在散文裡以 commit SHA 交代對應版本.

## 採用效果與驗證

預期效果:

- 減少不必要派工, context duplication 與整合重工;
- 降低 Plan verifier 無限來回;
- 讓 security 與 outcome verdict 的權限邊界可檢查;
- 讓 provider route, request source, 成本與 QC 結果能回溯;
- 壓縮過時 prompt, 同時保留 authority, stop, QC 與 deployment boundary.

目前能證明的是契約, 設定與測試已落地. 效能與可靠度差異仍需用相同 brief, 相同權限, 相同 acceptance 的 lifecycle replay, 加上 experience ledger 的 wall-clock, review/rework, token coverage 與失敗形態比較. 上游 v1.3.6-v1.3.8 的 Gate 提供了一套可借用的**方法**: 固定 prompt 檔, 對出貨 bytes 而非雜湊重跑, 每個 cell 記錄嘗試次數與成本硬上限, 通過後不補跑以美化計數. 方法可借, 數字不可借 - 那是它的契約在它的 client 版本上的觀察.

## 上游證據

- [Pilotfish v1.3.10 release](https://github.com/Nanako0129/pilotfish/releases/tag/v1.3.10), [v1.3.9 release](https://github.com/Nanako0129/pilotfish/releases/tag/v1.3.9)
- [CHANGELOG v1.3.5-v1.3.10](https://github.com/Nanako0129/pilotfish/blob/v1.3.10/CHANGELOG.md)
- 以下四條 Gate 連結釘在 v1.3.8, 因為它們是 v1.3.8 那一輪觀察的出處; tag 不可變, 不隨上游改版失效.
- [Spontaneous-dispatch Gate](https://github.com/Nanako0129/pilotfish/blob/v1.3.8/benchmarks/spontaneous-dispatch/README.md) (含 issue #29 的 recovery/topology traces)
- [Verifier-boundary Gate](https://github.com/Nanako0129/pilotfish/blob/v1.3.8/benchmarks/verifier-boundary/README.md) (v1.3.4 之後新增)
- [Baton-dispatch effect Gate](https://github.com/Nanako0129/pilotfish/blob/v1.3.8/benchmarks/baton-dispatch-effect/README.md)
- [Prompt-compression Gate](https://github.com/Nanako0129/pilotfish/blob/v1.3.8/benchmarks/prompt-compression/README.md), [budget.json](https://github.com/Nanako0129/pilotfish/blob/v1.3.8/benchmarks/prompt-compression/budget.json)
- [Deep Agents documentation](https://docs.langchain.com/oss/python/deepagents/overview)
