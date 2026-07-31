# Harness engineering 研究總結

> 對齊日期：2026-07-28。這是目前專案採用決策的入口；各來源的取證細節留在分題文件。

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
| Provider 選擇 | 外部排行榜給先驗；本機成本與失敗形態可能相反 | 外部資料只做先驗，本機 ledger 達樣本門檻後覆蓋 | 對實際工作流的可接受結果成本最重要 |
| Headroom 版本 | PyPI package 與 GitHub release tag 可能不同步 | 分別報告 package、release tag、PR 與 live service state | 避免把不同層級合成「目前版本」 |

## Pilotfish v1.3.0–v1.3.4 蒸餾結果

對齊上游 [v1.3.4 release](https://github.com/Nanako0129/pilotfish/releases/tag/v1.3.4)（tag commit `a4c585…`，2026-07-25）。v1.3.0 到 v1.3.4 存續下來、且適合本專案的精華已落為：

- shape-based batching 與 direct-execution brake；
- 最小完整驗收邊界與 outcome verifier quota；
- Plan anti-churn；
- fixed dispatch/result record 與 provenance-aware QC；
- security review／execution 分權；
- resident prompt 去重與 current-state 文件收斂。

這些控制目前已有靜態契約與測試。仍未證明的是長流程中的行為效果：中斷後恢復、連續 correction、互相衝突的 leaf 結果，以及真實 token／wall-clock 改善。這些應用 lifecycle replay 與 ledger 驗證，不能把「測試存在」寫成「效果已證明」。

## 時效性基準

- Deep Agents：PyPI stable `0.6.12`；beta `0.7.0b2`（2026-07-28 查核）。版本與託管產品狀態需在引用時重查。
- Headroom：PyPI `headroom-ai 0.32.1`；GitHub latest release tag `v0.32.0`；PR #1044 仍 open（2026-07-28 查核）。三者不可互換。
- OpenAI prompting guidance 使用目前 canonical 文件：[Latest model guide](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.6#prompting-best-practices)。
- Anthropic context guidance：[Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)。

## 文件索引

| 文件 | 用途 |
|---|---|
| [context-and-vendors.md](context-and-vendors.md) | 常駐 context 與官方供應商指引 |
| [resident-context-options.md](resident-context-options.md) | 常駐成本現況、可用槓桿與延後的 runtime-selection eval |
| [peer-harnesses.md](peer-harnesses.md) | Deep Agents、Pilotfish 原始碼與版本拆解 |
| [model-evidence.md](model-evidence.md) | route、effort、成本口徑與外部先驗 |
| [trap-experiments.md](trap-experiments.md) | 可重播的失敗情境與反證 |
| [local-experiments.md](local-experiments.md) | 本機任務結果 |
| [prompt-surface-census.json](prompt-surface-census.json) | deterministic resident／role surface 快照 |

## 驗證缺口

- [UNCERTAIN: Pilotfish-derived controls 尚未完成真實 lifecycle replay。]
- [UNCERTAIN: provider route cells 多數尚未達決策樣本門檻。]
- [UNCERTAIN: 外部 package、release、beta 與 PR 狀態會變動，引用前必須 live recheck。]
