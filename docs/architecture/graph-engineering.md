# Graph engineering: 多個 agent 的協作

**誰先做, 誰並行, 做完給誰.** 最外層, 包住 [loop](loop-engineering.md): 迴路管一個
agent 怎麼收斂, 拓撲管很多個迴路之間的順序, 擁有權與匯流.

這一層最貴的一句話是: **報告是一組待證主張, 不是證據.**

**管什麼.** 拓撲, 擁有權與狀態流: 誰派給誰, 誰擁有哪個 artifact, 結果怎麼回來.

**怎麼做.** main session 保留框架, 架構, 歧義, 整合與最終判斷; **直接執行是預設**, 只有
平行性, context 保護, fresh-context 獨立性, 或明顯較便宜的角色檔位值得那筆開銷時才派工.
派工的三個維度刻意分開, 不為每個題材新增 agent:

| 維度 | 決定什麼 | 本 repo 的實際值 |
|---|---|---|
| **Role** | 權限, 工具, 判斷與停止邊界 | 七個固定角色, 在 [`main/claude/agents/`](../../main/claude/agents/) |
| **Task class** | ledger 裡可比較的 cohort | 清單與各自的定義在 [metrics](../../main/.agents/skills/experience-ledger/references/metrics.md); 有幾個刻意不參與決策 |
| **Lens** | 這次要攻擊的接縫 | 語意接縫, 狀態與並行, 契約邊界, 測試有效性 |

三個維度為什麼要分開, 論證在 [playbook](../engineering-playbook.md#leaf-分派的三層契約).
`recon` (定位, 盤點, 摘要) 與 `review` (有界, 對抗式的唯讀審查, 必須指定 lens) 即使都由
`explore` 執行, 也不能併成同一筆 route 證據 —— 那會把兩種很不一樣的工作平均掉.

QC 把一件事制度化: **報告是一組待證主張, 不是證據.** 每次派工結束, main 依序做收件分級,
機械稽核, 抓詐欺清單 (含強制的 grep 覆核), 再四級裁決入帳. 派工的五個狀態每一個都要有
**實體承載物**, 不能只是散文約定 —— 沒有承載欄位的規則無法驗證.

**用什麼量.** dispatch ledger 記每一筆的 outcome, route 與 token; `weekly-integrity` 掃
有沒有 staged 了卻沒記錄的派工.

**已知怎麼壞.**

- **漂亮的報告會過關.** `s7` 這一格 (在交付物裡埋六種造假, 看無人稽核時抓不抓得到) 顯示
  說謊的報告可以全身而退. 另一格取證顯示, opus 檔位的 leaf 有約四成整行漏發修改依據, 十次
  裡有四次宣稱「沒有同型 bug」而其實有 —— 後者連格式稽核都看不出來, 因為那行格式完全
  正確, 只是內容是假的.
- **launcher 死了不等於派工死了.** bridge 的 job 比 launcher 長命, 重啟前不對帳就會對同一
  個 prompt 雙寫.
- **派工者說的 route 不等於實際跑的 route.** 所以 bridge 的路由改由 provider 自己的
  rollout 背書, 而不是由派的人自己宣稱.

**要動它得先拿出什麼.** 換 model 或 effort pin 要同 role, 同 task class, 同 route cell 的
本機 ledger 結果, 樣本不足就先探索; 外部排行榜只做先驗. 改部署映射要 manifest 列,
preflight, parity 與目標端證據四件齊全.

## 誰先做, 誰並行, 做完給誰

| 問題 | 這個 repo 的答案 |
|---|---|
| 誰先做 | 預設沒有人 —— 直接執行是預設, 派工要先通過三項成本測試 |
| 誰並行 | 以任務形狀 batching, 不以檔案數或 request bullet; 一個可寫 artifact 一個 owner |
| 做完給誰 | 回 main. leaf 不再派工, Claude 側由 `leaf-redispatch` 擋, Codex 側由 `max_depth = 1` |

## 還沒貼合的部分

- **並行幾乎沒有真實樣本.** ledger 裡絕大多數是單筆派工; 合批的判準寫得比用過的次數多.
- **跨 provider 的額度看不見.** verifier 額度只認 Claude 的拼法, 走 bridge 的那一側靠
  主 session 判斷.
