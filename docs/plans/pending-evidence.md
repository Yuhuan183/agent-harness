# 等證據的項目: 集中在一張表, 每項寫清楚等什麼與到了怎麼判

2026-08-31 起. 「等未來證據」的項目散在研究文的段落裡時沒有人負責看到期, 所以集中登記在這裡. 這裡只登記**等待本身** —— 條件原文與依據留在原地, link, don't repeat. 每項三欄: 等什麼, 什麼事件觸發判定, 判定後動作在哪寫著. 已經判定的項目移出這張表, 結果留在它指向的文件與 [landing-log](../research/landing-log.md).

入場檢查 (蒸餾自 rebelytics 3.0 與 3.1): 寫下任何「later」之前, 指名**哪一個具體觀察會改變決定, 它何時可能到** —— 指不出來就表示證據已經足夠或等待買不到東西, 兩種都是現在動手. 觸發事件還要**發生得了**: 問誰或什麼得動它才會發生, 那一方有沒有理由做恰好相反的事; 發生不了的條件不是等待, 是比較貴的靜默丟棄. 那種項目就地用今天有的替代證據結案, 或改押在會發生的觸發上.

## 一, 已定推翻條件在等的

| 等什麼 | 觸發 | 到了怎麼判 |
|---|---|---|
| 十個**新**戳章累積 | 任何 suite 的新結果列蓋到第十個新格式戳章 | 若沒有任何一個「只有一組動」的讀數, 分組連同組 digest 退回單一雜湊. 條文在 [cross-upstream-synthesis](../research/cross-upstream-synthesis.md) 發現一的第三代戳章節 |
| 再 30 個 run | 下一批 trap 批次跑完累積到 +30 | 若 ≤2 個 partial, `gate_lines.distance` 從文件層也移除. 條文在 [wording-effect-scale](../research/wording-effect-scale.md) 尺的最終帳 |

## 二, 等一次觀察的 (發生了才動工, 不排程)

| 等什麼 | 觸發 | 到了怎麼判 |
|---|---|---|
| No-ops 例行掃描的第一個真實命中 | 任何一次檢討發現「規則存在但整段期間零觸發」 | 照 [ledger 的 No-ops 節](../research/upstream-distillation-ledger.md#no-ops-我們量過-但沒有在掃)決定是否建掃描 |
| twin-guard 的一次真實漂移 | 雙生斷言在真實變更上抓到或漏掉一次 | 補真漂移測試, 案例記進 landing-log |
| skill 效用的第一批 task-observer 觀察 | telemetry 帳本累積到可讀的量 | 三條判準 (2026-08-17 先寫, 之後不改口): **三筆以上**觀察指名 `evidence-debugging` 或 `test-first-change` 之一, 那是它們有負載的證據; **三筆以上**摩擦的教訓落在它們的守備範圍而它們沒被載入, 那是觸發面的證據; **連續一個月**沒有任何一筆指向它們, 那是「不是這台機器的瓶頸」的弱證據, 屆時討論退役. 抓得到「用了但不好」, 抓不到「沒用而該用」, 這個代價照實記 |
| route cell 達樣本門檻 | 任一 role × task-class 格內有兩個 `model/effort` 都累積到 `min_samples = 10` | 2026-09-14 起比較軸從 provider 換成 tier (Codex 退場); 達標的格由 `revision_policy` 接手, 其餘維持探索 |
| 三十天內的下一次同形缺席誤讀 | 任何一次「探針覆蓋不足而結論已寫下」 | 2026-08-31 一天六次同形誤讀的處置停在措辭那一級 (`evidence-ladder` 加陽性對照與「一行式就是儀器」); 再發生就表示措辭這一級無效, 改問「哪些缺席宣稱可以被機械檢查」—— 候選是讓 `evidence-check.py` 對研究文裡的零/沒有/不存在句要求附一行探針指令. 檢討在 [landing-log](../research/landing-log.md) 08-31 節 |
| rebelytics 血緣 | 3.0 的儲存模型與改名同形出現可對回的第三方 issue, 或任一回報者被查明與本 repo 有關 | 09-06 探針: 公開引用查無, 3.1 儀器守則各對得到第三方 issue. 3.1 的票從 09-06 起計獨立; 3.0 同形維持佐證; 任一回報者被查明有關就全部退回. 見 [task-observer-upstream](../research/task-observer-upstream.md#血緣探針-2026-09-06-公開引用查無-而-31-的儀器守則各有自己的-issue) |

## 三之六, 成本儀器剩下的接線: 卡在歸因, 不是計算 (2026-08-31)

[landing-readiness](../research/landing-readiness.md) 的建議四寫「缺的不是框架也不是欄位定義, 是接線」. 接的時候發現只對了一半: **框架是完整的, 但它餓的是輸入, 而輸入拿不到**. `experience-report` 每個 cohort 已在算 `avg_api_cost_usd`, `avg_tokens_out`, `avg_total_tokens`, `avg_total_secs`, 口徑在 `model-evidence`; 沒有東西要新建. 輸入側, 164 筆帳本實測:

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
| `review_secs` / `rework_secs` | 不自動導出. 要嘛人工記, 要嘛承認這兩項永遠是空的 | 若三十天後仍是 0/N, 把 `avg_total_secs` 從報告移除 —— 一個永遠算不出來的欄位是雜訊 |

## 四, 蒸餾重查節奏

上游重查由 [research README 的時效性基準](../research/README.md#時效性基準)與 `scripts/upstream-pin-report.py` 驅動; 後者從 ATTRIBUTION 與那張表的 `pin` 句推導, sepia 與 ECC 這種還沒有 ATTRIBUTION 的來源靠表裡那一列被盯住. 下次重查時間到, 順帶讀 StoryScope 論文本文, 一趟做完. 跨上游整合已跑四輪, 計票與結論在 [synthesis](../research/cross-upstream-synthesis.md#第四輪整合-2026-09-06-開題與計票).
