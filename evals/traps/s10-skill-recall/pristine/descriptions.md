# Resident skill descriptions

This is the whole routing surface a Claude session carries: for each installed
skill, the `name` and `description` from its frontmatter. Nothing else about a
skill is in context until it is selected.

## baton-dispatch

Decide the dispatch shape — direct, one agent, bounded parallel, workflow, or isolated workspaces. Load once a dispatch is going ahead; it owns briefs, ownership, batching, collection, QC, and the fixed record formats.
觸發：已經決定要派工、「怎麼拆」「平行處理」「批次」「多個 writer」。
不觸發：小修改、已知目標查找、緊耦合除錯（留在 main 直接做）。

## evidence-debugging

Diagnose a reported defect from a reproduction you have actually run, and stop at the root cause unless repair was asked for. Invoke when the request says something is broken, failing, throwing, flaky, wrong, or slow, or asks to diagnose or debug — and in zh-TW: 出問題, 壞了, 掛了, 不會動, 有 bug, 很慢, 為什麼會, 查一下, 幫我看. Do not use for explaining code, reviewing a diff, refactoring, or writing a test for behaviour that already works.

## evidence-ladder

Establish that a technical claim is true — pick the cheapest sufficient level of evidence, avoid circular proof, calibrate instruments before trusting them, and record conclusions at the right durability.
觸發：「這個結論可靠嗎」「怎麼證明」「測試夠不夠」「我推導出 X」、下結論前的自我檢查、要把量測數字寫進文件、發現先前結論可能有誤。
不觸發：例行實作沒有爭議的結論、單純跑既有 gate、程式碼審查流程本身（用該專案的 review skill）。

## experience-ledger

Dispatch experience ledger and analysis — log each outcome after QC, accumulate role × provider metrics (AR/CR/RB/FR/QS), and steer data-driven provider choice.
觸發：記錄派工結果、依經驗選 provider、看派工指標、"log this dispatch"、"which provider is winning"。
不觸發：派工決策本身（baton-dispatch）、provider 規則（provider-routing）、token 用量分析（usage-report）。

## headroom-protocol

Compress an unusually large read-only blob when Headroom MCP tools exist and proxy routing is absent. Invoke automatically or explicitly for disposable analysis input, typically over 200 lines or several KB.
觸發：「壓縮這份輸出」「context 快爆了」、超大 JSON／log／表格／搜尋結果的唯讀處理。
不觸發：一般 CLI 工作、小型輸出、需要編輯的內容、精確錯誤診斷。

## provider-routing

Cross-provider routing — H/X profiles, GPT↔Claude fallback, codex bridge resolution, security routing, verifier triggers. Load before dispatching to GPT, on provider failure/handoff, or when deciding if a claim needs a verifier.
觸發：「派給 GPT/Codex」「換 provider」「fallback」「要不要 verifier」「安全審查找誰」、跨 provider 交接。
不觸發：單一 provider 的直接工作。

## readable-zh-tw

繁體中文可讀性：審查與改寫對外文字，砍廢話、校正中國用語與標點，讓它好讀。
觸發：「去 AI 味」「說人話」「這段好 AI」「改自然一點」「校對再發」「潤飾一下用字」、問版面怎麼排，或檢查電子報、社群貼文、銷售頁、文案、客服信、簡報、公告的語感。技術文檔（README、docs、skill）裡的中文敘述同樣適用。
不觸發：逐字翻譯、模仿特定品牌／個人 voice、事實查核、程式碼／log／設定檔。本 skill 管可讀性，不加個人風格。
Triggers: "de-AI this text", "make it sound human", "how should this be laid out", "polish this zh-TW copy before publishing"; also zh-TW prose in technical docs (README, docs, skills). Not for: literal translation, brand-voice mimicry, fact-checking, code/log/config.

## task-observer

Capture and review reusable skill-improvement observations. Invoke after skill-assisted work receives explicit dissatisfaction or a requested correction or rework (for example, 不滿意, 不符合, 不是我要的, 修正, 重做, unhappy, not what I asked, wrong, fix, redo, or rework), or when the user asks to record feedback, inspect the backlog, act on an observation, or review improvement opportunities. After handling the immediate correction, proactively ask once whether to record the feedback; write only with explicit consent. Do not invoke for ordinary task execution, background monitoring, or automatic skill updates.

## test-first-change

Add or change behaviour by writing the check that fails first, at a seam that reaches the observable result. Invoke when the request asks to implement, add, change or extend behaviour, to write or repair a test, or names TDD or test-first — and in zh-TW: 實作, 加上, 改掉, 擴充, 補測試, 修測試. Do not use for an unexplained defect (diagnose it first with evidence-debugging), for formatting or documentation-only edits, or for a change nothing could have failed on beforehand.
