# 在 Fable 5 上避免 fallback 到 Opus

我們只在 **main session** 用 Fable 5。這份文件的核心目的只有一個：**用 Fable 5 時，怎麼避免
被安全檢查切換到 Opus**——理想是自動化避免，不理想時至少讓它變成可觀察的暫停而非隱形漂移。

先澄清一個同名陷阱：這裡的「fallback」是 Anthropic 產品層的**安全旗標切換**（Fable → Opus），
不是本 harness 的**跨 provider 單跳**（provider 不可用時 GPT↔Claude）。兩者無關。

| 「fallback」兩義 | 觸發 | 目標 | 誰擁有 |
|---|---|---|---|
| Anthropic 安全切換（本文） | 安全檢查標記內容 | Fable 5 → **Opus 5** | 產品層，repo 管不到 |
| 本 harness 跨 provider（[provider-routing](../main/claude/skills/provider-routing/SKILL.md)） | provider／runtime 不可用 | GPT↔Claude 對應角色 | 本 repo |

> 目標模型：官方文章當時寫 Opus 4.8，現行是 **Opus 5**。模型會更新，但避免策略與目標版本無關。

## 為什麼可以靠派工避免（核心機制）

關鍵事實：安全檢查「reviews everything the model reads, not just your latest message」——它讀的是
**當前 session 的全部 context**（memory、檔案、web、先前訊息都算）。

由此推出避免的槓桿：

- Fable 只在 main session；**named roles 全部 pin 在 Opus**（契約禁用 Fable），而 Opus 正是
  fallback 的目標，對這個切換**免疫**。
- 所以把會觸發的內容**派到 Opus leaf 去做**，觸發內容就留在 **leaf 的 context**、不進 main。
  main session 的 context 保持乾淨，就不會被標記。

這不是新機制，而是 harness 既有「context protection」派工理由的新動機：以前是為了 token 預算與
main context 純度，現在多一個——**保持 Fable main session 不被標記**。

## 四類會觸發的內容（判斷依據）

派工前用這四類做啟發式判斷（來源：官方 support 文章）：

1. 攻擊性 cybersecurity——建 exploit／malware／攻擊工具（「expect high fallback rates」）。
2. 生物化學與生命科學——實驗方法、分子機制，甚至波及良性研究與醫療。
3. 蒸餾攻擊——含抽取模型的「summarized thinking」。
4. 窄域前沿 LLM 開發——分散式訓練基建、ML 加速器、非標準晶片 kernel。

命中任一類，預設把該段工作拆給 Opus leaf，而非在 Fable main session 直接處理。

## 自動化到什麼程度：誠實的可行性

**可以自動化的部分**（紀律 + 啟發式）：

- main session 對命中四類的工作，預設派 Opus leaf（`executor`／`security-executor`／`explore`），
  觸發內容不進 main。
- 交付整合時沿用既有紀律：**main 收結論不收 dump**——大型或敏感產物留在檔案／leaf，main 用
  路徑引用而非內嵌（與 RTK／Headroom 的「大輸出存檔後讀切片」同一條規則）。

**不能靠自動化保證的部分**（這是「不確定能不能實現」的答案）：

1. **沒有事前預言機**：無法 100% 預知某則訊息會不會被標記，啟發式只能逼近，不能證明。
2. **產物即敏感內容時整合會重新暴露**：若交付物本身就是觸發內容（可用 exploit、合成路線），
   一旦整合回 main 就重新暴露，下一則 main 訊息可能觸發。這類任務只能讓 main 引用檔案、
   永不內嵌；若連結論摘要都落在四類內，就無法在 Fable main 上安全整合。
3. **memory／connector／檔案的持久觸發**：若持久 context 裡就帶觸發內容，派工救不了，須清掉
   該來源。

結論：**可行的是「紀律 + 啟發式 + 安全網」，不是硬保證**。把它當成 context protection 的延伸，
不要當成一道關得死的 gate——關不死的 gate 會誘人相信假保證（與 [dispatch-lifecycle](dispatch-lifecycle.md)
「artifact 所有權仍屬判斷」同一個道理）。

## 安全網：關掉自動切換

避免失手時，讓後果**可觀察**。Claude Code：**Config > MODEL & OUTPUT →「Switch models when a
message is flagged」關掉**。關掉後被標記的請求「pauses the conversation instead of switching
models」——你會看到暫停而非默默換模型，然後可以：把該段拆給 Opus leaf、編輯訊息重試、或手動送
Opus。

理由與 harness 一貫原則一致：**絕不在使用者不知情下換模型跑**。暫停是乾淨的失敗，靜默切換是
隱形漂移，而 ledger 對 main-session 的模型切換沒有任何承載欄位可對照——關掉自動切換等同把
隱形漂移換成明確訊號。

## 切換後的行為（萬一發生）

- 切換後「the model picker stays on Opus for the rest of the conversation」；可手動切回 Fable。
- 但切回「may trigger the same block again because the original request is still part of it」——
  因為觸發內容還在 context。**編輯或移除那段內容**通常才解得掉，單純切回沒用。
- 計費：input 階段被擋全按 Opus；串流中被擋，擋前按 Fable、其餘按 Opus。

## 設計方向（未實作，供日後評估）

以下記錄做法與原理，尚未實作、也未決定要不要做。orchestration-plan 的未決項有指標。

### 方向一：軟性啟發式 dispatch 提示 hook

- **做法**：`UserPromptSubmit` hook 讀 main session 當前 prompt 文字，用關鍵訊號比對四類
  （cyber：exploit／payload／shellcode／CVE 武器化；bio/chem：合成路線／病原／分子機制；
  蒸餾：抽取 reasoning／summarized thinking；frontier LLM：加速器 kernel／分散式訓練基建）。
  命中就印出建議（**非 exit 2**）：「這段可能觸發 Fable→Opus，建議拆給 Opus leaf，main 只收
  結論」。只在 main 觸發（`agent_id` 為空）。
- **原理**：提示，不是 gate。三個理由——(a) 無法複製 Anthropic 的真實分類器，硬 gate 會誤擋
  正常工作；(b) 安全檢查讀全 context，hook 只看得到當前 prompt，看不到 memory／檔案／web，
  本質是**不完整覆蓋**，只能提示不能保證；(c) 符合 harness「診斷型 fail-open、狹窄才
  fail-closed」的分層，這種模糊判斷屬診斷型。
- **待決**：訊號清單怎麼定才不過度誤判；是否值得那筆維護成本 vs 直接靠 main 判斷。

### 方向二：把「fallback 避免」正式列為 dispatch payoff

- **做法**：現有 dispatch payoff 有四種（parallelism／context-protection／fresh-context／
  cheaper-tier）。可加一條約定：命中四類的工作，context-protection payoff 視為成立，main
  預設派 Opus leaf。
- **原理**：這其實是 context-protection 的既有情形，只是動機不同。所以傾向**只在本文件記錄**，
  不進常駐契約——加常駐規則有稀釋成本，而這條靠本文件按需揭露即可。
- **待決**：值不值得進常駐契約 vs 留按需文檔；會不會鼓勵過度派工。

### 方向三：routing 文件區分兩種 fallback

- **做法**：在 provider-routing 或 routing toml 加一句 cross-reference 指向本文。
- **原理**：消歧義，避免把安全切換誤當跨 provider 單跳。
- **待決**：provider-routing 預算已近上限，得先騰空間或放 `references/`。

### 方向四：main-session 模型稽核缺口

- **做法**：要讓 main-session 像 leaf 一樣有 route 證據，需要能讀「實際作答模型標示」的機器
  出口。
- **原理**：目前 ledger 對 main-session 的模型切換沒有承載欄位，靜默切換無從稽核。
- **待決**：阻塞於產品層未提供機器可讀出口，屬 [research](harness-engineering-research.md) 的
  「仍待本機驗證」。
