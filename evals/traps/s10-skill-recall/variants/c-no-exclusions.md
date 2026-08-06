# Resident skill descriptions

This is the whole routing surface a Claude session carries: for each installed
skill, the `name` and `description` from its frontmatter. Nothing else about a
skill is in context until it is selected.

## baton-dispatch

Decide the dispatch shape — direct, one agent, bounded parallel, workflow, or isolated workspaces. Load once a dispatch is going ahead; it owns briefs, ownership, batching, collection, QC, and the fixed record formats.
觸發：已經決定要派工、「怎麼拆」「平行處理」「批次」「多個 writer」。
不觸發：小修改、已知目標查找、緊耦合除錯（留在 main 直接做）。

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

## speak-human-tw

繁體中文去 AI 味改寫：審查與改寫對外文字，去除 AI 腔、校正中國用語與半形標點，讓文字讀起來像真人寫的。
觸發：「去 AI 味」「說人話」「這段好 AI」「改自然一點」「校對再發」，或檢查電子報、社群貼文、銷售頁、文案、客服信、簡報、公告的語感。
Triggers: "de-AI this text", "make it sound human", "polish this zh-TW copy before publishing".

## task-observer

Capture and review reusable skill-improvement observations. Invoke after skill-assisted work receives explicit dissatisfaction or a requested correction or rework (for example, 不滿意, 不符合, 不是我要的, 修正, 重做, unhappy, not what I asked, wrong, fix, redo, or rework), or when the user asks to record feedback, inspect the backlog, act on an observation, or review improvement opportunities. After handling the immediate correction, proactively ask once whether to record the feedback; write only with explicit consent. Do not invoke for ordinary task execution, background monitoring, or automatic skill updates.
