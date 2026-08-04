# Harness engineering 研究總結

> 對齊日期: 2026-07-28, Pilotfish 段於 2026-08-04 重查至 v1.3.8. 這是目前專案採用決策的入口; 各來源的取證細節留在分題文件.

## 現行結論

現代模型仍需要 harness，但 harness 應縮到「模型無法可靠自行維持、且能被驗證」的邊界：權限、派工深度、可寫 artifact 所有權、Plan 收斂、provider route、獨立驗證條件、可追溯結果與部署邊界。風格偏好、一般工程常識與重複提醒不應膨脹 resident prompt。

本專案的最佳平衡是：

1. main task 保有整合與最終判斷，direct execution 為預設；
2. 只因平行價值、context 保護或 fresh-context independence 派工；
3. 以任務形狀 batching，不以檔案數或 request bullets batching；
4. Plan 最多兩次自動實質修訂，之後讓使用者選擇；
5. outcome verifier 最多一個，放在最小完整驗收邊界；
6. Claude no-write roles 不給 Bash；需要命令的獨立 verdict 交給 Codex read-only sandbox；
7. provider/model 決策只用同 role、同 task class、同 route cell 的本機結果，樣本不足就探索；
8. Git 是可攜真相源；installer lock、憑證、session、服務狀態留在 machine-local。

## 來源衝突與裁決

| 議題 | 來源間衝突 | 專案裁決 | 理由 |
|---|---|---|---|
| 主動派工 | Pilotfish 鼓勵在合適形狀下主動 dispatch；精簡 resident prompt 傾向少規則 | 保留三項成本測試，未通過就 direct | 取得平行效益，同時避免 delegation tax |
| Batching | 上游示例偏向同形任務批次；一般 checklist 容易按 request bullet 拆分 | 依 shared context、artifact、dependency、verification surface 分組 | 降低重建 context 與整合成本 |
| Plan 迭代 | verifier 可持續要求修正；不中止會形成 churn | 同 readiness-unit 最多兩次自動實質修訂 | 把真正選項交回使用者，不假裝無限收斂 |
| Bash 唯讀 | shell allowlist 想保留可執行重現；security review 證明 parser 可被 callbacks、環境與 expansion 繞過 | Claude no-write roles 完全移除 Bash；命令驗證轉 Codex read-only sandbox | 能力邊界比解析任意 shell 可證明 |
| Prompt 壓縮 | Pilotfish benchmark 支持壓縮；vendor guidance 仍要求清楚結構與關鍵約束 | 移除重複／過時敘述，不刪除 authority、stop、QC 與安全邊界 | 壓縮是降低 resident tax，不是追求最短 |
| 壓縮的驗證方式 | 上游 v1.3.7 顯示 255 條短語斷言全數通過, 仍放進十二個語意缺陷; 本專案測試同樣以短語為主 | 壓縮常駐契約時另做逐句對照, 重點檢查連接詞, 範圍限定詞與否定詞 | 這三類改動不會動到任何被斷言的短語, 測試綠燈不構成證據 |
| Provider 選擇 | 外部排行榜給先驗；本機成本與失敗形態可能相反 | 外部資料只做先驗，本機 ledger 達樣本門檻後覆蓋 | 對實際工作流的可接受結果成本最重要 |
| Headroom 版本 | PyPI package 與 GitHub release tag 可能不同步 | 分別報告 package、release tag、PR 與 live service state | 避免把不同層級合成「目前版本」 |

## Pilotfish v1.3.0-v1.3.8 蒸餾結果

對齊上游 [v1.3.8 release](https://github.com/Nanako0129/pilotfish/releases/tag/v1.3.8) (tag commit `ad9600c...`, 2026-08-04). v1.3.0 到 v1.3.4 存續下來, 且適合本專案的精華已落為:

- shape-based batching 與 direct-execution brake；
- 最小完整驗收邊界與 outcome verifier quota；
- Plan anti-churn；
- fixed dispatch/result record 與 provenance-aware QC；
- security review／execution 分權；
- resident prompt 去重與 current-state 文件收斂。

v1.3.5-v1.3.8 的增量與本專案處置:

| 上游增量 | 本專案處置 |
|---|---|
| verdict 三分 CONFIRMED/REFUTED/INCONCLUSIVE | 已有等價, 雙 provider 一致 |
| 只有可重現的 P0-P2 blocker 能 refute, P3/P4 僅建議 | 收斂成一條判準: 反例要可重現**且會改變驗收結論**, 其餘列 `Advisory:` 照報不動 verdict; 不引進嚴重度分級 |
| 阻斷性修復共用五次 pass 預算 + candidate-state fingerprint | 已採五次上限; 指紋改成每 pass 自述上次之後改了什麼, 沒改就不重驗 |
| readiness epoch 與一次最終 fresh readiness check | 維持現行硬性兩次上限, 不放寬 |
| 常設 prompt 尺寸預算寫進測試 | 已有等價 (per-document 字數上限 + resident 總量 + role body budget), 另加規則條數/每條位元組/虛詞比例三項密度指標, 量測口徑不同 |
| dispatch brake 壓過 explicit opt-in | 已有等價 |

這些控制目前已有靜態契約與測試. 仍未證明的是長流程中的行為效果: 中斷後恢復, 連續 correction, 互相衝突的 leaf 結果, 以及真實 token/wall-clock 改善. 這些應用 lifecycle replay 與 ledger 驗證, 不能把「測試存在」寫成「效果已證明」. 上游 v1.3.6 之後已公開自己的 Gate replay 方法與成本, 方法可借用, 數字屬於它的契約與 client 版本, 不能當成本專案的證據.

## 時效性基準

- Pilotfish: latest release tag `v1.3.8`, tag commit `ad9600c...` (2026-08-04 查核). 上游發版頻率高於本文件的重查頻率, 引用前先確認 tag.
- Deep Agents：PyPI stable `0.6.12`；beta `0.7.0b2`（2026-07-28 查核）。版本與託管產品狀態需在引用時重查。
- Headroom：PyPI `headroom-ai 0.32.1`；GitHub latest release tag `v0.32.0`；PR #1044 仍 open（2026-07-28 查核）。三者不可互換。
- OpenAI prompting guidance 使用目前 canonical 文件：[Latest model guide](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.6#prompting-best-practices)。
- Anthropic context guidance：[Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)。

## 方向與落地紀錄

這節回答「下一步做什麼, 為什麼是這一步」. 排序原則是**證據強度 × 成本**, 不是影響力大小.
理由: 影響力是估出來的, 前兩者查得到; 用估出來的量當主排序鍵, 等於讓最會講故事的那條排第一.

新方向沿用同一格式, 每條只寫三行: 做什麼, 為什麼排這裡, 什麼會推翻它. 沒有推翻條件的建議
不是結論, 是偏好. 落地時先跑推翻條件, 成立就照該條自己寫的降級方案走.

### 已落地 (2026-08-04)

原本七條方向一次做完. 每條都先跑自己的推翻條件, 成立就照該條寫好的降級方案走, 不硬做 —
這是這份清單的設計意圖, 不是偷工. 唯一調動過的順序是把第 4 條排在第 5 條之前: 第 5 條會鼓勵
壓縮, 先開閘再補防護等於刻意製造暴露窗口.

| # | 方向 | 推翻條件查核 | 落地形式 |
|---|---|---|---|
| 1 | `mech-executor` 強制行只留 `AUTH:` | **成立, 但理由不同**: 逐 commit 查核顯示兩端契約從未出現 INTENT/TWINS, 原本「規則自己製造它要防的失敗」的前提是錯的 | 目標狀態本來就成立且已被測試鎖住; 交付改成修正兩份寫錯因果的文件 |
| 2 | 解開 support pin 取樣死結 | 不成立: 兩端三個 profile 逐一查過, 沒有任何一個覆寫 support role 的 frontmatter pin | 走「承認由使用者偏好決定」那條. `model-routing.toml` 撤回 `n >= 10` 引用, 改記 `support_pin_evidence`; 論述見 [model-evidence.md](model-evidence.md) |
| 3 | 有界重驗: pass 預算與指紋 | 不成立: ledger 有一條 2026-07-28 的四次 verifier 派工鏈 (同一目標, 4.5 小時內), 三次上限會誤殺合法工作 | 兩端 dispatch skill 加五次上限, 並要求每個 pass 先講出上一次之後改了什麼; 沒改的候選不重驗 |
| 4 | 壓縮的語意守門機械化 | 不成立: `c143b72` 自己的 commit message 就是一筆本機壓縮語意缺陷 | 新增 `scripts/contract-operator-delta.py`, 永遠 exit 0 的附證腳本, 不是 gate |
| 5 | 常駐預算改為正規化密度 | 不成立: 換算後兩份契約在新指標下都有餘裕, 不是隱性收緊 | 密度指標**加在**字數上限之外, 字數上限一格未動 (見下) |
| 6 | REFUTED 門檻收斂 | 不成立: ledger 九筆 verifier 記錄裡沒有 advisory 級發現退回好結果的實例 | 兩端 `verifier` 契約各加一句判準, 不引進嚴重度分級 |
| 7 | lifecycle replay 存活判準 | **部分成立**: 判準第 3 項確實不需要 live session 就量得到 | 寫成 [lifecycle-replay.md](lifecycle-replay.md), 並註明第 3 項已有 `weekly-integrity` 在看; replay 仍未開跑 |

第 5 條的落地與原本寫的不同, 值得說清楚: 密度指標是**加上去**而不是取代字數上限. 要讓密度
先綁定, codex 那份的字數上限得往上拉約四分之一, 而沒有證據支持把常駐層放大到那個程度. 這條
方向自己的推翻條件禁止把收緊偷渡進換算, 同一條理由也禁止偷渡放寬. 換掉的是**調高字數上限的
判準**: 三項密度都還在上限內的擴充, 買到的是更好的句子而不是更多字.

同批完成的還有 trap 在 Opus 5 上的重跑 (2026-08-04): s7/s8 各 3 seeds, s9 補到 11 seeds,
結果見 [model-evidence.md](model-evidence.md) 與 `evals/traps/*/README.md`.

### 待辦方向

只剩一條: **跑 lifecycle replay**. 前置的存活判準已經寫完, 缺的是逐情境的 reach marker 與
實際執行, 條件與「還不能做的事」見 [lifecycle-replay.md](lifecycle-replay.md).

### 明確不做的事

| 不做 | 理由 |
|---|---|
| 移植上游的 P0-P4 嚴重度分類法 | 換到的是同一個失效的更細表述, 代價是六個角色檔的規則條數 |
| 把上游 Gate 的數字當本專案證據 | 那是它的契約在它的 client 版本上的觀察; 方法可借, 數字不可借 |
| 把語意守門做成 fail-closed gate | 合法變動遠多於違法變動, 高誤報會導致繞過或白名單 |
| 在存活判準之前開跑 lifecycle replay | 會產出被後續文件引用, 且引用者看不出是空的數據 |

## 文件索引

| 文件 | 用途 |
|---|---|
| [context-and-vendors.md](context-and-vendors.md) | 常駐 context 與官方供應商指引 |
| [resident-context-options.md](resident-context-options.md) | 常駐成本現況、可用槓桿與延後的 runtime-selection eval |
| [peer-harnesses.md](peer-harnesses.md) | Deep Agents、Pilotfish 原始碼與版本拆解 |
| [model-evidence.md](model-evidence.md) | route、effort、成本口徑與外部先驗 |
| [trap-experiments.md](trap-experiments.md) | 可重播的失敗情境與反證 |
| [local-experiments.md](local-experiments.md) | 本機任務結果 |
| [lifecycle-replay.md](lifecycle-replay.md) | replay 開跑前的存活判準; 尚無 replay 結果 |
| [prompt-surface-census.json](prompt-surface-census.json) | deterministic resident／role surface 快照 |

## 驗證缺口

- [UNCERTAIN: Pilotfish-derived controls 尚未完成真實 lifecycle replay; 上游 v1.3.6-v1.3.8 的 Gate 數據是它自己契約的 reachability 觀察, 不轉移到本專案. 開跑前的存活判準已寫在 [lifecycle-replay.md](lifecycle-replay.md).]
- [UNCERTAIN: 第 3 與第 6 條的推翻條件已於 2026-08-04 查過 ledger (131 筆, 其中 verifier 9 筆), 但這是單機單人的樣本; 「沒觀察到」在這個量級上是弱證據.]
- [UNCERTAIN: 方向排序是設計判斷, 不是實驗結果; 每條的「推翻條件」才是可檢驗的部分, 落地紀錄裡的查核結果同樣只在當時的 artifact 上成立.]
- [UNCERTAIN: provider route cells 多數尚未達決策樣本門檻。]
- [UNCERTAIN: 外部 package、release、beta 與 PR 狀態會變動，引用前必須 live recheck。]
