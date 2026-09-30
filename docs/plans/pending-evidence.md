# 等證據的項目: 集中在一張表, 每項寫清楚等什麼與到了怎麼判

2026-08-31 起. 「等未來證據」的項目散在研究文的段落裡時沒有人負責看到期, 所以集中登記在這裡. 這裡只登記**等待本身** —— 條件原文與依據留在原地, link, don't repeat. 每項三欄: 等什麼, 什麼事件觸發判定, 判定後動作在哪寫著. 已經判定的項目移出這張表, 結果留在它指向的文件與 [landing-log](../research/landing-log.md).

入場檢查 (蒸餾自 rebelytics 3.0 與 3.1): 寫下任何「later」之前, 指名**哪一個具體觀察會改變決定, 它何時可能到** —— 指不出來就表示證據已經足夠或等待買不到東西, 兩種都是現在動手. 觸發事件還要**發生得了**: 問誰或什麼得動它才會發生, 那一方有沒有理由做恰好相反的事; 發生不了的條件不是等待, 是比較貴的靜默丟棄. 那種項目就地用今天有的替代證據結案, 或改押在會發生的觸發上.

## 一, 已定推翻條件在等的

目前沒有. 原有兩項 (十個新戳章, 再 30 個 trap run) 都要靠新的 eval 批次才會前進, 而 09-15 之後沒有排程, 照入場檢查的「發生不了」2026-09-30 結案, 維持現狀; 讀數在 [landing-log](../research/landing-log.md#2026-09-30-收斂-等不到的等待結案-六個來源停追-一個永遠算不出來的欄位退場).

## 二, 等一次觀察的 (發生了才動工, 不排程)

| 等什麼 | 觸發 | 到了怎麼判 |
|---|---|---|
| No-ops 例行掃描的第一個真實命中 | 任何一次檢討發現「規則存在但整段期間零觸發」 | 照 [ledger 的 No-ops 節](../research/upstream-distillation-ledger.md#no-ops-我們量過-但沒有在掃)決定是否建掃描 |
| twin-guard 的一次真實漂移 | 雙生斷言在真實變更上抓到或漏掉一次. 2026-09-30 起只剩一對雙生: 專案層的 `CLAUDE.project.md` 與 `AGENTS.project.md`, 由 `test_project_layer.py` 的 `test_both_templates_ask_the_same_facts` 盯槽位對齊 (原本那對 Claude/Codex 契約樹隨 09-14 Codex 退場消失) | 補真漂移測試, 案例記進 landing-log |
| skill 效用的第一批 task-observer 觀察 | **2026-09-30 結案, 改道.** | 08-17 起 57 個真實 session 裡, 明確的不滿用語出現 5 次 (3 個 session), task-observer 事後被叫起 0 次, 帳本檔從未建立; 同期糾正是靠 memory 留下並當場修掉. 所以 task-observer 改成只能用 `/task-observer` 手動叫 (`disable-model-invocation: true`, 說明不再常駐), `evidence-debugging` 與 `test-first-change` 的效用改看 `skillUsage` 次數與 replay eval. **2026-12-29 回頭看**: 若 `/task-observer` 這段期間一次都沒被叫, 討論整個退役; 原本獨立一列的 rebelytics 血緣查證 (09-06 起 3.1 的票計獨立, 3.0 同形維持佐證) 09-30 併進這一次, 因為它只在還要從 rebelytics 採規則時有意義, 而 09-30 重查 12 條 0 採用 |
| route cell 達樣本門檻 | 任一 role × task-class 格內有兩個 `model/effort` 都累積到 `min_samples = 10` | 2026-09-14 起比較軸從 provider 換成 tier (Codex 退場); 達標的格由 `revision_policy` 接手, 其餘維持探索 |

## 三之六, 成本儀器剩下的接線: 卡在歸因, 不是計算 (2026-08-31)

[landing-readiness](../research/landing-readiness.md) 的建議四寫「缺的不是框架也不是欄位定義, 是接線」. 接的時候發現只對了一半: **框架是完整的, 但它餓的是輸入, 而輸入拿不到**. `experience-report` 每個 cohort 已在算 `avg_api_cost_usd`, `avg_tokens_out`, `avg_total_tokens` (當時還有 `avg_total_secs`, 09-30 移除), 口徑在 `model-evidence`; 沒有東西要新建. 輸入側, 164 筆帳本實測:

```text
api_cost_usd     1/164     ← 幾乎沒有
review_secs      3/164
rework_secs      0/164     ← 從來沒有
tokens_in/out  109/164
token_scope full 90/164
```

兩條看起來可以自動化的路都不能走. **從 stub 導出 `review_secs`**: 那個間隔常被「還沒有人記」主導而不是被審查主導 (帳本旁 23 筆 pending stub 擱了三天), 只在間隔夠小時導出又會系統性低估. **從 proxy log 取實際成本**: session id 在 `proxy_inbound_request` 的 headers 裡, token 與成本數字在 PERF 行, 沒有任何一行同時帶兩者; 用時間鄰近去接是啟發式不是查表.

已經做了的那一段: `context_proxy` 欄位 (同日) 讓往後每一筆知道自己有沒有經過壓縮 proxy, 那是歸因的前提. 而 2026-08-31 11:04 之前的 cache 讀數經過帶 `#2085` 缺陷的 Headroom 0.36.5, 帳本分不出哪筆受影響, 所以一律不得直接重用 (行為類結果不受影響, 它們從報告正文評分).

| 項目 | 下一步 | 通過條件 |
|---|---|---|
| 成本歸因 | 查 Headroom 有沒有辦法讓 PERF 行帶 session id (`x-headroom-session-id` 標頭要控制 Claude Code 送出的標頭, 我方目前做不到), 或讓 `/stats` 逐 session 分列 | 有: 接一支批次前後取差值的腳本; 沒有: 記「本 repo 量不到逐批成本」, 並停止在文件裡承諾成本數字 |

## 四, 蒸餾重查節奏

上游重查由 [research README 的時效性基準](../research/README.md#時效性基準)與 `scripts/upstream-pin-report.py` 驅動; 後者從 ATTRIBUTION 與那張表的 `pin` 句推導, sepia 這種還沒有 ATTRIBUTION 的來源靠表裡那一列被盯住; ECC 與 Trellis 2026-09-30 移到[不再追](../research/README.md#不再追的來源-2026-09-30-停), 報告不再拿它們比 head. 下次重查時間到, 順帶讀 StoryScope 論文本文, 一趟做完. 跨上游整合已跑四輪, 計票與結論在 [synthesis](../research/cross-upstream-synthesis.md#第四輪整合-2026-09-06-開題與計票).
