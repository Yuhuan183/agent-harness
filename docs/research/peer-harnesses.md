# 同業 agent harness 拆解

> 對齊日期: Pilotfish 段 2026-08-21 (仍是 v1.3.10); pilotfish-codex 段 2026-08-21 (1.7.1); Deep Agents 段 2026-08-20 (0.7.7). 只保留會影響本專案設計的存續結論.

## 這份文件回答什麼

看兩個同類專案, 各自解決什麼問題, 本專案抄了什麼, 為什麼有些不抄.

| 專案 | 它是什麼 | 本專案主要拿走什麼 |
|---|---|---|
| LangChain Deep Agents | 一組可組合的 middleware 與 state boundary, 不是固定流程 | allowlist 優於 denylist; report 與 tool output 視為 untrusted observation |
| Pilotfish | 一套完整的 agent 派工契約, 版本迭代快 | 派工形狀, Plan anti-churn, verdict 三分, prompt 尺寸當常設預算 |

貫穿全文的一條限制: **方法可借, 數字不可借.** 上游的 Gate 數字是它的契約在它的 client 版本上的觀察, 引用時必須連同它自己標的限定一起引.

## LangChain Deep Agents

查核版本: PyPI stable `0.7.7`; CLI `deepagents-code` 0.1.58 (2026-08-19); `deepagents-acp` 0.0.10. 三個 package 各自發版, 版本序不同步, 引用前分開報.

2026-08-08 那次記的是: 0.7.x 全是修補與小功能, 沒有新的 middleware; 值得記的變動在 CLI 0.1.52 的 Hooks v2 與 HITL 拒絕理由改寫成給模型看的形式 - 最後這項與 Anthropic auto mode 的 deny-and-continue 是同一件事, 兩個獨立實作收斂 (見 [研究摘要方向 5](README.md#待辦方向)).

### 2026-08-20 重查: 主線移到 session 身分

0.7.5 → 0.7.7 與 CLI 0.1.54 → 0.1.58 之間, 三個 release 講同一件事:

- `0.7.6` 摘要時把對話歷史 offload 到**另一個 session id**;
- CLI `0.1.56` 修「強制壓縮分叉」, 保住 `session_id`;
- CLI `0.1.55` 與 `deepagents-acp 0.0.10` 加上 session 的持久化與重新設定.

PyPI 摘要也改寫了, 現在把 context management 與 long-term memory 放進第一句.

**為什麼這一段值得查而不是抄**: 本專案的 `dispatch_id` 是 `<session>:<agent>`, 而
`weekly-integrity` 的孤兒偵測靠它配對. 壓縮若換掉 session id, 壓縮前後的紀錄會分屬兩個
session, 對帳就會憑空生出孤兒.

**查了, 這裡不成立**: 本 repo 一次經歷過壓縮的工作階段, project 目錄下當天只有一個
transcript, id 全程未變, 沒有分叉出兄弟檔. **但那是代理指標** —— hook 看到的 `session_id`
才是真正的載體, 而該日沒有任何派工, 所以 `delegation.jsonl` 與 pending 都沒有事件可對.
要確立得等一次「壓縮之後才派工」的真實情況.

CLI 另外加了 `/context` 用量報告 (`0.1.55`) 與 `/offload` 後的總量 (`0.1.57`). 那正是本
專案 context 層寫下的第一條落差 (動態流入沒有儀器). **方向可借, 現在不做**: 這裡連「一次
典型工作階段流入多少」的基線都沒有, 先做儀器只會做出一支沒有校準的儀器.

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

### 2026-08-21 重查: 上游沒有動

最後一次 push 是 2026-08-07T22:26Z, 最新 release 仍是 v1.3.10 (2026-08-07). 也就是說
上一次對齊之後**上游一次都沒有動**, 下面整段維持有效, 不需要重讀.

值得記下來是因為「沒有變」和「沒有查」在文件上長得一樣. 這一行讓下一個人知道是哪一種.

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

## pilotfish-codex 1.5-1.7 (Codex CLI 分支)

[miyago9267/pilotfish-codex](https://github.com/miyago9267/pilotfish-codex) 從
Nanako0129/pilotfish 改編到 Codex CLI, 2026-08-21 首次進入本文件. 對齊到 1.7.1
(2026-08-11, 最後 push 同日).

**先講版本序**: 它自己走語意版號, 上游版本只當來源引用 —— 分支在 1.7.1 而本體在 v1.3.10,
兩個數字沒有可比性. 安裝的版本戳在 `AGENTS.md` policy block 裡的 HTML 註解
(`<!-- pilotfish-codex vX.Y.Z -->`), 與本專案用 manifest 加 parity 檢查是同一類做法.

### 蒸餾結果

| 分支的設計 | 本專案現況 | 裁決 |
|---|---|---|
| 七個角色: `scout`, `plan-verifier`, `executor`, `mech-executor`, `security-reviewer`, `security-executor`, `verifier` | 同樣七個, 只有 `explore` 對 `scout` 的命名不同 | **獨立收斂, 但只算兩票**. 本專案的七個角色在 2026-07-20 初版就存在, 早於 07-22 採用 Pilotfish 兩天, 所以我們這一側不是從那裡來的; 而這個分支繼承自 Pilotfish, 所以它和 Pilotfish 是同一票. 見[跨上游整合](#跨上游整合-2026-08-21) |
| review intent 每回合可選 `fast`/`default`/`strict`, 但**不得覆蓋必要核准與安全閘** | 逃生口同樣不繞過核准; 見[授權](../architecture/architecture.md#授權-每一道機制停在誰手上) | **獨立收斂**, 不動 |
| **review-service circuit breaker**: reviewer/verifier 收據缺席時一次有界重試, 然後進入明確等待狀態; 且「review 服務失效不是使用者決策」, 不得據以宣告 readiness, 驗證, 憑證或對外寫入 | 原本只規定 verifier 的額度與放置點, 沒有一條說 verifier 沒回來時該怎麼辦 | **已落地** (2026-08-21). 與 [cablate/baton 的 fall-back 規則](#cablatebaton-baton-dispatch-的上游)合併成一條, 兩支 dispatch skill 各帶一份 |
| 三個 tier (luna/terra/sol) 之中 **terra 沒有任何角色在用** —— luna 跑例行執行與驗證, sol 只給 `plan-verifier` 與安全審查那類窄邊界 | H/X 兩檔 | **佐證現況**. 一個獨立實作定義了三檔又空著中間那檔, 是「檔位不是越多越好」的外部證據 |
| intent routing 先於角色: `execute` / `explore_then_plan` / `co_discover` 三種初始模式由請求形狀決定 | 無等價; client 自身的 plan mode 已承擔「廣泛請求先唯讀」 | **不採用**, 與 v1.3.9「互動模式先於工作者」同一裁決 |
| `direction_checkpoint`: 續行 / 轉向 / 回退 / 再問, 四個出口 | 計數式的「同一 readiness-unit 兩次自動修訂後交還使用者」 | **不同機制, 同一關切**. 我們的是次數上限, 它的是決策點; 目前不換 |
| grounding floor (禁無據臆測) 與 stopping ceiling (禁失控分析) | evidence ladder 與最短驗證迴路 | 已落地, 口徑不同 |
| Windows: 避開 POSIX-only 假設, 並用 LF 正規化維持 fixture hash 一致 | 指紋機制沒有跨平台考量 | **不採用但記著**. 本專案目前單平台; 真要跨平台時, 換行正規化是指紋會先壞掉的地方 |

### 為什麼分支值得單獨看

它不是翻譯. 兩週內從 1.5.1 走到 1.7.1, 動的是安裝架構 (Codex marketplace layout,
PowerShell installer, 跨平台 CI), 執行期切分 (Hybrid runtime: 常駐 root bootstrap 最小化,
其餘打包成 Codex plugin 的 skill), 以及上面那個 circuit breaker —— 每一項都是本體沒有的.

**常駐最小化那一項尤其是獨立收斂**: 它把 orchestration 拆成「一定要在場的 bootstrap」加上
「按需載入的 skill」, 理由和本專案把契約留常駐, `baton-dispatch` 按需載入完全一樣
(見 [context 層](../architecture/context-engineering.md)).

1.5.1 還公開了一個負面結果: native Sol transport 跑得穩, 但切換的品質/成本自評
`5/10`, 而 release note 明說這一版不宣稱該項達標. 願意把自評分數寫進 release note 的
上游, 它的正面數字才有重量.

## cablate/baton (baton-dispatch 的上游)

[cablate/baton](https://github.com/cablate/baton), 2026-08-21 重查. 最新 release
v0.1.1 (2026-07-10), 最後 push 2026-07-16, 之後沒有再動.

`baton-dispatch` 的本文寫著它是「a local distillation of cablate/baton v0.1.1 plus a
scope fix」. 那個 scope fix 是 release 之後的 commit
[`0ab4d2ec5c69820001eeac2a12fab2c87fd3e943`](https://github.com/cablate/baton/commit/0ab4d2ec5c69820001eeac2a12fab2c87fd3e943)
(2026-07-16, "Prevent delegated scope expansion"), 已經落在
`baton-dispatch` 的 Run design 段. **完整 SHA 記在這裡而不是 skill 本文**, 因為部署檔裡的
裸短 SHA 讀的人解不開 ([docs/README.md 規則 9](../README.md)).

### 2026-08-21 逐條核對: 兩條沒有本地對應

把上游七節的每一條規則對回本專案的兩支 dispatch skill 與兩份常駐契約, 十條裡八條有等價
寫法, 兩條沒有:

| 上游規則 | 本專案 | 處置 |
|---|---|---|
| Fall back to direct execution when delegation infrastructure is unavailable or repeatedly fails | 只有**派工前**的成本判準 (「payoff 不明就直接做」), 沒有**派工後持續失敗**的規則. 既有的 stop 全在 leaf 內部 (3 次修復-驗證循環, 2 次徒勞查找) | **採用** |
| Treat completion of the current vertical slice as a checkpoint; do not automatically dispatch the next phase | 有五次 pass 上限與兩次自動修訂上限, 沒有一條說做完一個 slice 不等於可以開下一個 | **採用** |

第一條和 [pilotfish-codex 的 circuit breaker](#pilotfish-codex-15-17-codex-cli-分支)
是同一個洞的兩面: 上游 baton 說「退回自己做」, codex 分支說「一次有界重試, 然後明確等待,
而且不得宣告已驗證」. **兩個彼此獨立的上游指向同一處**, 這比任一邊單獨說更有份量, 所以
落地的寫法取兩者的交集加上後者那句最鋒利的 —— 失去一個 agent **不是使用者的決策**.

### 這次查核暴露的程序問題

`baton-dispatch` 沒有 ATTRIBUTION 檔, 而另外四支蒸餾來的 skill 都有. 上游只寫在 skill
本文的一句話裡, 所以第一次找的時候 (查 ATTRIBUTION 檔與 docs) 找不到, 得使用者直接指出來.
四支有 ATTRIBUTION 的 skill 共用同一個上游 (mattpocock/skills), 而
[`scripts/upstream-recheck.sh`](../../scripts/upstream-recheck.sh) 與
[蒸餾帳本](upstream-distillation-ledger.md) 也都只綁那一個上游 —— 也就是說,
**這個 repo 有一套可覆核的蒸餾程序, 但它只覆蓋一個上游**, baton 與兩支 Pilotfish 都在外面.

## 跨上游整合 (2026-08-21)

前面每一節回答的是「這個上游有沒有我們漏掉的東西」. 這一節回答的是不同的問題: **四個上游
加起來, 對我們的設計說了什麼**. 按層做, 不按上游做.

參與的四個: mattpocock/skills (寫作與除錯技藝), cablate/baton (派工治理),
Nanako0129/pilotfish 與其 Codex 分支 miyago9267/pilotfish-codex, LangChain Deep Agents.

### 一, 收斂要先數血緣, 不然會多算票

**pilotfish-codex 是 Pilotfish 的 fork, 所以它和 Pilotfish 是同一票, 不是兩票.**
比較表一直有記「改編自 Nanako0129/pilotfish」, 但沒有一句說這件事會影響證據的權重 ——
於是 2026-08-21 的紀錄把七個角色寫成「兩邊各自演化」, 讀起來像三方同意.

查了日期之後結論仍然成立, 但理由不同: 本專案的七個角色在 **2026-07-20 初版**就存在
(executor, Explore, mech-executor, plan-verifier, security-executor, security-reviewer,
verifier), 而 Pilotfish 是 **07-22** 才進到這個 repo. 我們這一側**不是**從那裡來的, 所以
「我們」與「Pilotfish 血系」確實是兩個獨立來源 —— 兩票, 不是三票.

**推翻條件**: 找得到 2026-07-20 之前的紀錄顯示角色切分參考過 Pilotfish, 這一條就垮.

### 二, 每一個同業都有而我們沒有的, 只有一件: 成本

| 上游 | 成本在它那裡是什麼 |
|---|---|
| Pilotfish | v1.3.6 起公開自己的 Gate replay 方法**與成本** |
| pilotfish-codex | v6 benchmark: weighted tokens, median wall time, equivalent cost; 另有品質校正後的成本度量 |
| cablate/baton | 開篇就是 dispatch brake —— 派工要先過自己的 overhead |

三個派工上游各自把成本當成**一等的, 被量測的軸**. 本專案有成本判準 (Cost test 就是
baton 那條), 但**沒有一份文件擁有它**: context 層講常駐預算, graph 層講 routing 與付費點,
playbook 講注意力稅, 三處各談一面, 而「這樣做值不值得」沒有歸屬.

這件事原本掛在待辦清單上, 性質是「純粹的裁決題, 沒有時間壓力」. **三個獨立上游都有而我們
沒有, 把它從家務事變成缺口.**

**推翻條件**: 寫得出一段話說明為什麼本專案的形狀不需要一個成本的擁有者 —— 例如成本已經
完全被那三處的機制覆蓋, 沒有任何決策落在它們之間. 寫不出來, 就是缺一份文件.

### 三, 我們有而沒有人有的: 雙生對稱 —— 是優勢, 但守衛有洞

沒有任何一個上游把同一套規則同時維護在兩個 provider 上並要求逐條對齊. pilotfish-codex
看起來最接近, 但它是**移植**不是雙生: 它自己走版號, 明說上游版本只當來源引用.

這是本專案的邊, 而且不是空談 —— `test_contracts.py` 五十支測試裡有 **28 支同時斷言兩側**.

**但它的一次真實漂移不是測試抓到的.** 2026-08-19 那次 (deliverable-path 條款兩側規則不同,
Claude 說了該怎麼做而 Codex 只說了禁止) 是**在同一輪 review 裡讀出來的**. 測試斷言的是
片語, 而一條規則可以兩側片語都在, 意思卻不同 —— 這正是 `contract-operator-delta` 存在的
理由.

**推翻條件**: 往後如果有一次雙生測試在**真實漂移**上變紅 (不是改名), 這個機制就是承重的;
如果漂移持續是靠人讀出來的, 那 28 支斷言是文件, 不是閘.

### 四, 上游彼此不同意的地方: 角色之上要不要有一層互動模式

- **Pilotfish v1.3.9 與其分支**: 有. 先決定互動形狀 (execute / explore_then_plan /
  co_discover), 再指派角色.
- **cablate/baton**: 沒有. 選 execution primitive, 沒有 intent 層.
- **Deep Agents**: 沒有. 用 middleware 組合能力.

本專案兩次都判**不採用**, 理由是 client 自己的 plan mode 已經承擔「廣泛請求先唯讀」.

**不同意本身就是結論**: 這不是同業的既定做法, 三條血系裡兩條沒有它. 我們的拒絕因此不是
逆勢, 是多數 —— 而先前兩次拒絕的理由各自寫在自己那一列, 沒有人看得出這件事.

**推翻條件**: 三條血系裡有第二條加上互動模式層, 或者本機出現一次「因為沒有互動模式層而
走錯形狀」的可觀察案例.

### 這次整合沒有做的

只用了 `peer-harnesses.md` 這一份的內容加上日期查證. `clause-pricing`,
`model-evidence`, `lifecycle-replay` 與 `trap-experiments` 四份共約 38,000 字
的本機實驗證據**沒有進到這一輪** —— 它們回答的是「我們自己量到什麼」, 而這一輪問的是
「同業說了什麼」. 兩者要對起來是下一輪的事.

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
