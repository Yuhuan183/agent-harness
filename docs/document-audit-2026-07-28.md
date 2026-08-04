# 專案文檔與開發指引統一稽核

稽核 ID: `DOC-AUDIT-2026-07-28-ENVELOPE`
比較基準: `728936f`
範圍定義: [document-inventory.json](document-inventory.json)

## 結果

原文件有實質偏移, 並非只有文字老舊. 最重要的偏移是:

- Claude verifier 宣稱唯讀, 但持有可被繞過的 Bash parser;
- Codex 分析文檔宣稱 `sync.sh` 會備份, 實作其實不備份;
- `.skill-lock.json` 被追蹤/部署, 與 machine-local installer ownership 衝突;
- hook gate 數量與清單過時;
- current Plan 混有已完成 migration, 無效命令與歷史決策;
- Pilotfish 採用表仍把已落地控制寫成缺漏;
- Headroom 的 PyPI package, GitHub release tag, open PR 與 live state 被混成一個版本概念;
- dispatch 固定紀錄與 ledger 無法表示 Codex 啟動 Claude CLI 的來源.

以上均已回饋到角色契約, provider routing, deployment manifest, ledger schema, 研究總結與 current Plan.

## 六維度評估

| 維度 | 稽核前 | 修正後 |
|---|---|---|
| 邏輯鏈 | readiness, outcome, security 大致分離, 但 executable verification 權限與「唯讀」宣稱衝突 | capability-aware: Claude 做靜態 fresh-context review; 命令 verdict 交給 Codex read-only sandbox |
| 流程 | current Plan 混入歷史, rollback 語意未對齊單一 commit | current state/history 分離; 本輪採 R1 hunk rollback, 最後單一 commit |
| 語言 | 中英標點, gate 數量, backup/merge 說法不一致 | 以台灣繁中敘述現況; 命令與 identifier 保持英文; 關鍵詞彙統一 |
| 用詞 | profile, priority, model, package, release, live state 容易互換 | 每一層分開命名與取證 |
| 模組邊界 | installer state 進入 Git; shell parser 承擔 sandbox 責任 | Git/machine-local, tool allowlist/sandbox, review/execution 邊界明確 |
| 可驗證性 | 多數是靜態測試, 但文檔把機制存在寫成效果已證明 | 靜態落地與行為效果分開; 保留 lifecycle replay 與 ledger 缺口 |

## 來源衝突

完整裁決見[研究總結](research/README.md#來源衝突與裁決). 對本專案最重要的三個平衡:

1. **direct-first 與 proactive dispatch**: 只在淨收益為正且工作形狀可穩定描述時派工.
2. **prompt 壓縮與必要約束**: 刪重複, 歷史與一般常識; 保留 authority, capability, stop, QC, deployment boundary.
3. **可重現與安全隔離**: 不再用 shell parser 模擬 sandbox; 需要命令時改用真正的 read-only execution boundary.

## 預期效果

- 安全: 移除可繞過 parser 後, Claude no-write role 的 mutation surface 從「依賴命令解析正確」降為「根本沒有 Bash」.
- 效率: current Plan 與研究入口縮短, 降低每次 session 的過時 context 與決策重建.
- 一致性: 部署, ledger, provider routing 與文檔使用同一組 ownership/request-source vocabulary.
- 可維護性: inventory test 會在新增 current guidance 卻未被審查規則涵蓋時失敗.

## 尚未證明

- [UNCERTAIN: 尚無相同 brief/權限/acceptance 的前後 lifecycle benchmark, 因此不能量化 token 或 wall-clock 改善.]
- [UNCERTAIN: provider route cells 多數未達本機決策樣本門檻.]
- [UNCERTAIN: 這次只更新 Git source; 沒有 deploy, 所以 HOME 仍可能保留舊 hook/installer snapshot.]
