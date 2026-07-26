# Fable 5 安全 fallback 與 routing 整合性

Fable 5 在對話中可能被自動切換到 Opus 4.8——這是 Anthropic 的**安全旗標**機制，不是這個
harness 的跨 provider fallback。兩者同名但完全不同，先把這點分清楚，否則會誤讀 routing。

| 「fallback」的兩個意思 | 觸發 | 目標 | 誰擁有規則 |
|---|---|---|---|
| **本 harness 的 fallback**（[provider-routing](../main/claude/skills/provider-routing/SKILL.md)） | provider／runtime 不可用，單跳跨 provider | GPT↔Claude 對應角色，然後停 | 本 repo 的 routing |
| **Anthropic 的安全 fallback**（本文） | 安全檢查標記內容 | Fable 5 → Opus 4.8 | Anthropic 產品層，repo 管不到 |

來源：[Why Claude switched models in your conversation with Fable 5](https://support.claude.com/en/articles/15363606-why-claude-switched-models-in-your-conversation-with-fable-5)（2026-07 讀取）。

## 規則摘要

**觸發**——自動安全檢查在四個領域標記請求：攻擊性 cybersecurity（建 exploit／malware／攻擊工具，
「expect high fallback rates」）、生物化學與生命科學、蒸餾攻擊（含抽取模型的「summarized
thinking」）、窄域前沿 LLM 開發（分散式訓練基建、ML 加速器、非標準晶片 kernel 等）。

關鍵：檢查「reviews everything the model reads, not just your latest message」，所以一次切換
「can be triggered by content you didn't type」——memory、connector、web search、檔案都算。

**行為**——落到「next-most-capable model, Claude Opus 4.8」（Opus 自己也可能再擋）。切換後
「the model picker stays on Opus for the rest of the conversation」。可手動切回 Fable 5，但
「switching back may trigger the same block again because the original request is still part of
it」；編輯前一則訊息「often helps」。會顯示切換通知，回覆標示實際作答的模型。

**控制**——Claude Code 於 **Config > MODEL & OUTPUT** 把「Switch models when a message is
flagged」關掉；關掉後被標記的請求「pauses the conversation instead of switching models」。
其他選項：編輯後重試、手動送 Opus、對正當防禦 cyber 申請 Cyber Verification Program、用
Send feedback 回報誤判。API「isn't automatic」，需自行 opt-in。

**計費**——input 階段被擋：全按 Opus 費率並計入額度。串流中被擋：擋前的 input／token 按
Fable 費率，其餘按 Opus 費率。文章未列具體數字配額。

## 對本 harness 的暴露面

好消息是暴露面已被既有設計收窄：**只有 main session**。Named roles 契約禁用 Fable
（`model-routing.toml` 的 `role_frontmatter`：「contract forbids Fable in named roles」），
Fable 只用於 main session 的 H/X profile，bridge 走 GPT／Codex。所以 leaf 派工不受這個
安全 fallback 影響。

但 main session 正是做框架、架構、整合與最終判斷的地方。三個具體風險：

1. **靜默模型漂移**。main session 若在 Fable 上被切到 Opus，任何「這段編排是哪個模型做的」
   的自我認知就錯了。harness 對 leaf 有 route 證據（bridge 的 `rollout-verified`、native 的
   `resolver-assumed`），但**對 main session 的模型切換沒有任何承載欄位**——ledger 記不到。
   這是一個已知缺口（[dispatch-lifecycle](dispatch-lifecycle.md) 的承載物準則對 main 不適用）。
2. **security 工作最容易觸發**。security review 會把 exploit 與 abuse-path 內容帶回 main 的
   context；因為檢查讀全部 context，之後**任何一則**不相關訊息都可能觸發 fallback。
3. **context 累積**。長 session 一旦讀進敏感內容就持續「hot」，fallback 可能在後續回合才發作，
   且切回 Fable 會因原內容仍在 context 而再次觸發。

## 避開指引

1. **關掉自動切換（第一要務）**。Config > MODEL & OUTPUT →「Switch models when a message is
   flagged」off。理由與 harness 自己的原則一致：**絕不在使用者不知情下換模型跑**。暫停是可
   觀察的乾淨失敗；靜默切換是隱形漂移，而 harness 沒有能對照 main-session 模型的證據。把隱形
   漂移換成明確暫停，等同於 harness 一貫的「查不到就停，不要假裝清白」。
2. **security-adjacent 工作別掛在 Fable main session**。改用 Opus main session，或走 CP-first
   把 security 角色派到 Codex／GPT 側（named roles 本就在 Opus，不受影響）。
3. **context 衛生**。CTF／安全工程預期會暫停或改用 Opus main；不要在同一個長 session 裡先讀
   大量敏感內容再期待 Fable 全程作答。
4. **要確認 Fable 真的作答時，看回覆的模型標示**——ledger 不記 main-session 切換，這是手動查核。

## 給 harness 的後續建議（未實作）

- routing 文件可加一句，明確區分兩種「fallback」，避免讀者把安全切換誤當成跨 provider 單跳。
- 若要讓 main-session 模型可稽核，需要一個能讀「實際作答模型標示」的承載欄位——目前產品層
  未提供機器可讀出口，屬於 [research](harness-engineering-research.md) 的「仍待本機驗證」類缺口。
